"""Evidence-preserving retrieval. No learned or hand-calibrated feasibility scores."""

import hashlib
import json
from .chemistry import PARAMETERS, canonical_reaction, fingerprint, cosine
from .curation import validate
from .schema import VERSION


def build_index(data, include_drafts=False):
    report = validate(data)
    if report["errors"]:
        raise ValueError("数据校验失败：" + "; ".join(report["errors"][:10]))
    contexts = {r["context_id"]: r for r in data["contexts"]}
    groups, skipped = {}, []
    for row in data["experiments"]:
        context = contexts[row["context_id"]]
        reason = None
        if context["record_status"] == "示例":
            reason = "example"
        elif context["record_status"] != "已核对" and not include_drafts:
            reason = "draft_context"
        elif row.get("structure_status") != "已核对":
            reason = "unverified_structure"
        if reason:
            skipped.append({"measurement_id": row["measurement_id"], "reason": reason})
            continue
        reaction = canonical_reaction(row["reaction_smiles"])
        fp = fingerprint(reaction)
        if not fp:
            skipped.append({"measurement_id": row["measurement_id"], "reason": "zero_difference"})
            continue
        # Preserve different product channels; merge measurements only within this assay/product.
        key = (row["assay_id"], reaction, row.get("product_role"), row["outcome"])
        if key not in groups:
            groups[key] = {"assay_id": row["assay_id"], "context_id": row["context_id"],
                           "canonical_reaction": reaction, "fingerprint": fp,
                           "context": context, "measurements": []}
        groups[key]["measurements"].append(row)
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
    return {"schema_version": VERSION, "parameters": PARAMETERS,
            "dataset_sha256": hashlib.sha256(raw).hexdigest(),
            "include_drafts": include_drafts, "entries": list(groups.values()), "skipped": skipped}


def query(index, reaction, top_k=10, catalysis_mode=None, before=None, exclude_source=None):
    if top_k < 1:
        raise ValueError("top-k 必须大于零")
    if index.get("parameters") != PARAMETERS:
        raise ValueError("索引指纹参数/RDKit版本与当前环境不同，请重新构建")
    vector = fingerprint(reaction)
    if not vector:
        raise ValueError("查询反应净变化指纹为零")
    hits = []
    for entry in index["entries"]:
        context = entry["context"]
        if catalysis_mode and context["catalysis_mode"] != catalysis_mode:
            continue
        if exclude_source and context["source"].lower().removeprefix("https://doi.org/") == exclude_source.lower().removeprefix("https://doi.org/"):
            continue
        if before and (not context.get("date_evidence") or not context.get("first_public_date") or context["first_public_date"] >= before):
            continue
        hits.append({"reaction_similarity": cosine(vector, entry["fingerprint"]),
                     **{k: v for k, v in entry.items() if k != "fingerprint"}})
    hits.sort(key=lambda x: (-x["reaction_similarity"], x["assay_id"], x["canonical_reaction"]))
    return {"query": canonical_reaction(reaction), "metric": "cosine_signed [-1,1]",
            "interpretation": "反应结构相似度；不是酶催化成功概率。未检出记录仅为该实验的目标转化。",
            "eligible_entries": len(hits), "hits": hits[:top_k]}
