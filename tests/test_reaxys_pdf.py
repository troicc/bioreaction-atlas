from bioreaction_atlas.reaxys_pdf import parse_export, summarize

EXPORT = """Copyright © 2026 Elsevier Life Sciences IP Limited
1/570 2026-09-20 09:34:04
Rx-ID: 41267686 View in Reaxys 1/1000
Yield Conditions & References
91 % With hemin, β-cyclodextrin in water, Time= 120h, T= 35 °C , Green chemistry
Xu, Xiaofei; Li, Chang; Tao, Zhihao; Pan, Yuanjiang; Advanced Synthesis and Catalysis; vol. 357; nb. 14-15;
(2015); p. 3341 - 3345
View in Reaxys
86 % With Cu(OAc)2 in dichloromethane, T= 25 °C
Keipour, Hoda; Ollevier, Thierry; Organic Letters; vol. 19; nb. 21; (2017); p. 5736 - 5739
View in Reaxys
Rx-ID: 42172835 View in Reaxys 2/1000
Yield Conditions & References
95 % Time= 12h, Inert atmosphere, Reflux
Zheng, Yang; Xu, Xinfang; European Journal of Organic Chemistry; vol. 2016; nb. 22; (2016); p. 3872 - 3877
View in Reaxys
"""


def test_each_reaction_becomes_one_record():
    records = parse_export(EXPORT)
    assert [r['reaxys_reaction_id'] for r in records] == ['41267686', '42172835']


def test_a_pdf_export_never_claims_a_structure():
    assert all(r['reaction_smiles'] is None for r in parse_export(EXPORT))


def test_every_literature_condition_is_kept_separately():
    records = parse_export(EXPORT)
    assert len(records[0]['conditions']) == 2
    assert [c['yield_percent'] for c in records[0]['conditions']] == ['91', '86']


def test_authors_are_not_left_inside_the_condition_sentence():
    condition = parse_export(EXPORT)[0]['conditions'][0]
    assert condition['conditions_raw'].endswith('Green chemistry')
    assert 'Xu, Xiaofei' not in condition['conditions_raw']


def test_citation_fields_are_split_out():
    condition = parse_export(EXPORT)[0]['conditions'][0]
    assert condition['journal'] == 'Advanced Synthesis and Catalysis'
    assert condition['year'] == '2015' and condition['volume'] == '357'
    assert condition['pages'] == '3341 - 3345'


def test_boilerplate_lines_are_dropped():
    blob = ' '.join(c['conditions_raw'] for r in parse_export(EXPORT) for c in r['conditions'])
    assert 'Copyright' not in blob and 'View in Reaxys' not in blob


def test_summary_counts_sources_not_just_rows():
    report = summarize(parse_export(EXPORT))
    assert report['reactions'] == 2 and report['condition_rows'] == 3
    assert report['distinct_journals'] == 3
    assert report['year_range'] == ['2015', '2017']


def test_an_empty_or_unrelated_document_yields_nothing():
    assert parse_export('some other pdf entirely') == []
