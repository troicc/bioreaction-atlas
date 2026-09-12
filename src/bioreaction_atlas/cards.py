"""Human-readable evidence cards, without inventing a mechanism or success claim."""
from pathlib import Path
import re
from rdkit.Chem import rdChemReactions
from rdkit.Chem.Draw import rdMolDraw2D


def markdown(value):
    return str(value or 'Not reported').replace('\n', ' ').replace('|', '\\|').replace('<', '&lt;').replace('>', '&gt;')


def draw_reaction(text, path):
    reaction = rdChemReactions.ReactionFromSmarts(text, useSmiles=True)
    if reaction is None:
        raise ValueError('Cannot draw reaction')
    drawer = rdMolDraw2D.MolDraw2DSVG(1100, 260)
    drawer.DrawReaction(reaction)
    drawer.FinishDrawing()
    Path(path).write_text(drawer.GetDrawingText())


def write_cards(result, out_dir):
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    draw_reaction(result['query'], folder/'query.svg')
    lines = ['# Reaction-neighbor evidence cards', '',
             'These are retrieved structural precedents, not newly validated reactions or calibrated feasibility predictions.', '',
             '![Query reaction](query.svg)', '']
    for i, hit in enumerate(result['hits'], 1):
        diagram = f'neighbor_{i:02d}.svg'
        draw_reaction(hit['reaction_smiles'], folder/diagram)
        lines += [f"## {i}. {markdown(hit['record_id'])}", '',
                  f"Similarity: **{hit['similarity']:.4f}**. Domain: {markdown(hit['domain'])}.", '',
                  f'![Retrieved reaction]({diagram})', '', '| Source | Location | Review state | Cofactor / metal |',
                  '|---|---|---|---|']
        # Preserve every evidence record in JSON; render the first five to keep cards readable.
        for e in hit['evidence'][:5]:
            lines.append(f"| {markdown(e['source'])} | {markdown(e['source_locator'])} | {markdown(e['review_status'])} | {markdown(e.get('context',{}).get('metal_cofactor'))} |")
        if len(hit['evidence']) > 5:
            lines += ['', f"{len(hit['evidence'])} source rows in total; full provenance is preserved in the retrieval JSON."]
        e = hit['evidence'][0]
        c = e.get('context', {})
        lines += ['', f"Reported conditions: {markdown(c.get('conditions_raw'))}.",
                  f"Reported activation/mechanism: {markdown(c.get('mechanism'))}.",
                  f"Outcome status: {markdown(e.get('outcome'))}.", '',
                  '**Transfer assessment:** Pending chemistry review. Check substrate activation, metal/ligand requirements, reaction partners, medium and competing pathways against the seed enzyme system.', '']
    file = folder/'evidence_cards.md'
    file.write_text('\n'.join(lines)+'\n')
    return str(file)
