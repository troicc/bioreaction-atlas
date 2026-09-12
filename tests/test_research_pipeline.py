from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
from bioreaction_atlas.encoders import Encoder, pairwise_similarity
from bioreaction_atlas.corpus import encode_corpus, load_index, find_neighbors
from bioreaction_atlas.evaluation import evaluate, validate_protocol, condition_agreement, _metrics


@pytest.fixture
def corpus():
    records=[]
    for ident, reaction, domain in [('S1','CCO>>CC=O','enzymatic'),
        ('C1','CCCO>>CCC=O','nonenzymatic'),('C2','CC(=O)O.N>>CC(=O)N.O','nonenzymatic'),
        ('C3','C=C>>CC','nonenzymatic')]:
        records.append({'record_id':ident,'reaction_smiles':reaction,'domain':domain,'source':'TEST_'+ident,
                        'source_locator':'test fixture only','review_status':'checked','first_public_date':'2018-01-01',
                        'date_evidence':'fixture only','context':{},'outcome':'检出'})
    return {'corpus_version':'1.0','purpose':'test_fixture_only','records':records}


def protocol_for(info):
    ids={e['evidence'][0]['record_id']: e['record_id'] for e in info['entries']}
    return {'benchmark_version':'1.0','cutoff_date':'2020-01-01','candidate_pool_protocol':'synthetic test only',
            'freeze_note':'synthetic test only','seed_entry_ids':[ids['S1']],
            'candidates':[{'candidate_id':c,'entry_ids':[ids[c]]} for c in ['C1','C2','C3']],
            'events':[{'event_id':'E1','paper_id':'P1','first_public_date':'2021-01-01','date_evidence':'fixture',
                       'mapping_evidence':'fixture','candidate_ids':['C1']},
                      {'event_id':'E2','paper_id':'P2','first_public_date':'2021-02-01','date_evidence':'fixture',
                       'mapping_evidence':'outside candidate coverage in fixture','candidate_ids':[]} ]}


@pytest.mark.parametrize('backend',['morgan','substrate','drfp'])
def test_encoders_retrieval_and_hash_integrity(corpus,tmp_path,backend):
    folder=tmp_path/backend
    info=encode_corpus(corpus,folder,backend)
    assert len(info['entries']) == 4
    result=find_neighbors(folder,'CCO>>CC=O',domain='enzymatic')
    assert result['hits'][0]['similarity'] == pytest.approx(1)
    assert not find_neighbors(folder,'CCO>>CC=O',domain='missing')['hits']
    with (folder/'vectors.npz').open('ab') as f:
        f.write(b'corruption')
    with pytest.raises(ValueError,match='checksum'):
        load_index(folder)


def test_review_and_example_filters(corpus,tmp_path):
    corpus['records'][0]['review_status']='example'
    corpus['records'][1]['review_status']='imported'
    a=encode_corpus(corpus,tmp_path/'strict')
    b=encode_corpus(corpus,tmp_path/'explore',allow_unreviewed=True)
    assert len(a['entries'])==2 and len(b['entries'])==3


def test_reversal_distinguishes_directional_baseline():
    x=Encoder('morgan').encode(['CCO>>CC=O','CC=O>>CCO'])
    assert pairwise_similarity(x,x)[0,1] == pytest.approx(-1)
    # Standard DRFP is symmetric in reaction direction; document rather than hide this property.
    y=Encoder('drfp').encode(['CCO>>CC=O','CC=O>>CCO'])
    assert pairwise_similarity(y,y,'tanimoto')[0,1] == pytest.approx(1)


def test_zero_vectors_not_compared():
    with pytest.raises(ValueError,match='Zero'):
        pairwise_similarity(np.zeros((1,3)), np.ones((2,3)))


def test_temporal_metrics_retain_uncovered_events(corpus,tmp_path):
    info=encode_corpus(corpus,tmp_path)
    protocol=protocol_for(info)
    result=evaluate(tmp_path,protocol,ks=[1,3],bootstrap=20)
    assert result['candidate_coverage']==0.5
    assert result['metrics']['structure']['overall_recall_at_k']['3']==0.5
    assert result['metrics']['structure']['covered_event_recall_at_k']['3']==1
    assert result['metrics']['uniform_random_expectation']['overall_recall_at_k']['1']==pytest.approx(1/6)
    assert result['metrics']['structure_plus_conditions']['overall_recall_at_k']==result['metrics']['structure']['overall_recall_at_k']


@pytest.mark.parametrize('mutate',[
    lambda p,i: i['entries'][0]['evidence'][0].update(first_public_date='2021-01-01'),
    lambda p,i: i['entries'][0]['evidence'][0].update(date_evidence=None),
    lambda p,i: i['entries'][0].update(domain='patent_reference'),
    lambda p,i: p['seed_entry_ids'].append('missing'),
    lambda p,i: p['events'][0].update(first_public_date='2019-01-01'),
    lambda p,i: p['events'][0].update(candidate_ids=['unknown']),
    lambda p,i: p.update(candidate_pool_protocol=''),
    lambda p,i: i['parameters'].update(backend='rxnfp'),
])
def test_temporal_protocol_rejects_leakage_and_unreviewed_sources(corpus,tmp_path,mutate):
    info=encode_corpus(corpus,tmp_path)
    protocol=protocol_for(info)
    mutate(protocol,info)
    with pytest.raises(ValueError):
        validate_protocol(protocol,info)


def test_ties_are_not_broken_using_candidate_ids():
    events=[{'event_id':'E','paper_id':'P','candidate_ids':['z']}]
    m=_metrics({'a':0,'b':0,'z':0},events,[1,2,3])
    assert m['overall_recall_at_k']['1']==pytest.approx(1/3)
    assert m['overall_recall_at_k']['2']==pytest.approx(2/3)
    assert m['events'][0]['expected_best_rank']==2


def test_condition_features_keep_missing_distinct():
    a={'metal':{'value':'Cu'},'activation':{'value':'radical'}}
    b={'metal':{'value':'cu'},'activation':{'value':'Lewis acid'}}
    r=condition_agreement(a,b)
    assert r['score']==0.25
    assert r['matched_fields']==['metal']
    assert r['missing_fields']==['light','medium']


@pytest.mark.integration
def test_official_rxnfp_weights_and_batched_inference():
    model=Path('data/local/public/rxnfp')
    if not model.exists():
        pytest.skip('Run scripts/fetch_public_assets.py to obtain pinned official weights')
    encoder=Encoder('rxnfp',model)
    batch=encoder.encode(['CCO>>CC=O','CCCO>>CCC=O'],batch_size=2)
    alone=encoder.encode(['CCO>>CC=O'],batch_size=1)
    assert batch.shape==(2,256) and np.isfinite(batch).all()
    assert np.allclose(batch[0],alone[0],atol=1e-5)
    # Numerical reference published in the official RXNFP README, using its exact input.
    original='Nc1cccc2cnccc12.O=C(O)c1cc([N+](=O)[O-])c(Sc2c(Cl)cncc2Cl)s1>>O=C(Nc1cccc2cnccc12)c1cc([N+](=O)[O-])c(Sc2c(Cl)cncc2Cl)s1'
    with encoder.torch.inference_mode():
        reference=encoder.model(**encoder.tokenizer(original,return_tensors='pt')).last_hidden_state[0,0,:5].numpy()
    expected=[-2.0174953937530518,1.7602033615112305,-1.3323537111282349,-1.1095019578933716,1.2254549264907837]
    assert np.allclose(reference,expected,atol=1e-5)
    with pytest.raises(ValueError,match='token limit'):
        encoder.prepare('C'*600+'>>CC')
