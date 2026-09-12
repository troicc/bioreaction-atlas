import argparse
import csv
import json
from pathlib import Path
from .curation import read_dataset, validate, write_json
from .schema import metadata, TABLES


def main(argv=None):
    p = argparse.ArgumentParser(description="BioReaction Atlas: 文献录入与反应检索基线")
    sub = p.add_subparsers(dest="command", required=True)
    template = sub.add_parser("template", help="生成字段字典及空白 CSV")
    template.add_argument("--out", default="templates")
    template.add_argument("--language", choices=['zh', 'en'], default='zh')
    merge = sub.add_parser('merge', help='Merge Chinese/English curator files without overwriting conflicts')
    merge.add_argument('inputs', nargs='+')
    merge.add_argument('--prefixes', nargs='+')
    merge.add_argument('--out', required=True)
    check = sub.add_parser("validate", help="校验 xlsx/CSV目录/JSON")
    check.add_argument("input")
    check.add_argument("--out", required=True, help="校验报告 JSON")
    check.add_argument("--normalized", help="仅在无错误时保存标准 JSON")
    build = sub.add_parser("index", help="构建已核对结构的检索索引")
    build.add_argument("input")
    build.add_argument("--out", required=True)
    build.add_argument("--include-drafts", action="store_true")
    search = sub.add_parser("query", help="检索反应结构近邻")
    search.add_argument("index")
    search.add_argument("reaction")
    search.add_argument("--out", required=True)
    search.add_argument("--top-k", type=int, default=10)
    search.add_argument("--mode", choices=["酶催化", "非酶催化", "无催化剂对照"])
    search.add_argument("--before", help="仅取有日期核查来源且早于 YYYY-MM-DD 的记录")
    search.add_argument("--exclude-source")
    refs = sub.add_parser('import-references', help='Import pinned public references for local exploration')
    refs.add_argument('--legacy', required=True)
    refs.add_argument('--patents', required=True)
    refs.add_argument('--limit', type=int, default=2000)
    refs.add_argument('--seed', type=int, default=17)
    refs.add_argument('--out', required=True)
    curated = sub.add_parser('curated-corpus', help='Convert validated intake to the multi-encoder corpus format')
    curated.add_argument('input')
    curated.add_argument('--out', required=True)
    enc = sub.add_parser('encode', help='Build a reusable structural/RXNFP matrix index')
    enc.add_argument('corpus')
    enc.add_argument('--backend', choices=['morgan', 'substrate', 'drfp', 'rxnfp'], default='morgan')
    enc.add_argument('--model-dir')
    enc.add_argument('--allow-unreviewed', action='store_true')
    enc.add_argument('--batch-size', type=int, default=32)
    enc.add_argument('--out', required=True)
    neighbors = sub.add_parser('neighbors', help='Query a multi-encoder matrix index')
    neighbors.add_argument('index_dir')
    neighbors.add_argument('reaction')
    neighbors.add_argument('--model-dir')
    neighbors.add_argument('--domain')
    neighbors.add_argument('--exclude-source')
    neighbors.add_argument('--top-k', type=int, default=10)
    neighbors.add_argument('--out', required=True)
    map_parser = sub.add_parser('map', help='Render offline interactive and PNG reaction maps')
    map_parser.add_argument('index_dir')
    map_parser.add_argument('--method', choices=['pca', 'tsne'], default='tsne')
    map_parser.add_argument('--out', required=True)
    card = sub.add_parser('cards', help='Render retrieval evidence with reaction structures')
    card.add_argument('results')
    card.add_argument('--out', required=True)
    evaluation = sub.add_parser('evaluate', help='Run a frozen discovery-event retrieval protocol')
    evaluation.add_argument('index_dir')
    evaluation.add_argument('protocol')
    evaluation.add_argument('--condition-weight', type=float, default=0.15)
    evaluation.add_argument('--k', nargs='+', type=int, default=[1,5,10])
    evaluation.add_argument('--out', required=True)
    args = p.parse_args(argv)
    try:
        if args.command == "template":
            from .localization import localized_metadata
            localized = localized_metadata(args.language)
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            write_json(out / "schema.json", localized)
            for name, spec in localized['tables'].items():
                with (out / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as fh:
                    csv.writer(fh).writerow([f["label"] for f in spec["fields"]])
            print(f"已生成字段字典与空白 CSV：{out}")
        elif args.command == 'merge':
            from .merge import merge_datasets
            data = merge_datasets(args.inputs, args.prefixes)
            write_json(args.out, data)
            print(f"Merged {len(data['contexts'])} contexts and {len(data['experiments'])} measurements")
        elif args.command == "validate":
            data = read_dataset(args.input)
            report = validate(data)
            report["counts"] = {k: len(data.get(k, [])) for k in TABLES}
            write_json(args.out, report)
            if report["errors"]:
                print(f"发现 {len(report['errors'])} 个错误：{args.out}")
                return 1
            if args.normalized:
                write_json(args.normalized, data)
            print(f"校验通过；{len(report['warnings'])} 项待补信息。{report['counts']}")
        elif args.command == "index":
            from .retrieval import build_index
            index = build_index(read_dataset(args.input), args.include_drafts)
            write_json(args.out, index)
            print(f"索引 {len(index['entries'])} 个实验/产物条目，跳过 {len(index['skipped'])} 条测量")
        elif args.command == 'query':
            from datetime import date
            from .retrieval import query
            if args.before:
                if len(args.before) != 10:
                    raise ValueError("before 必须为 YYYY-MM-DD")
                date.fromisoformat(args.before)
            result = query(json.loads(Path(args.index).read_text()), args.reaction,
                           args.top_k, args.mode, args.before, args.exclude_source)
            write_json(args.out, result)
            print(f"检索到 {len(result['hits'])} 个结果：{args.out}")
        elif args.command == 'import-references':
            from .corpus import import_references
            data = import_references(args.legacy, args.patents, args.limit, args.seed)
            write_json(args.out, data)
            print(f"Imported {len(data['records'])} unreviewed reference rows")
        elif args.command == 'curated-corpus':
            from .corpus import curated_corpus
            write_json(args.out, curated_corpus(read_dataset(args.input)))
        elif args.command == 'encode':
            from .corpus import encode_corpus
            data = json.loads(Path(args.corpus).read_text())
            index = encode_corpus(data, args.out, args.backend, args.model_dir, args.allow_unreviewed, args.batch_size)
            print(f"Encoded {len(index['entries'])} unique reactions; excluded {len(index['excluded'])} source rows")
        elif args.command == 'neighbors':
            from .corpus import find_neighbors
            result = find_neighbors(args.index_dir, args.reaction, args.top_k, args.model_dir, args.domain, args.exclude_source)
            write_json(args.out, result)
            print(f"Returned {len(result['hits'])} neighbors")
        elif args.command == 'map':
            from .maps import render_map
            print(render_map(args.index_dir, args.out, args.method))
        elif args.command == 'cards':
            from .cards import write_cards
            print(write_cards(json.loads(Path(args.results).read_text()), args.out))
        elif args.command == 'evaluate':
            from .evaluation import evaluate
            result = evaluate(args.index_dir, json.loads(Path(args.protocol).read_text()), args.k, args.condition_weight)
            write_json(args.out, result)
            print(f"Evaluated {result['event_count']} discovery events; coverage={result['candidate_coverage']:.3f}")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"错误：{exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
