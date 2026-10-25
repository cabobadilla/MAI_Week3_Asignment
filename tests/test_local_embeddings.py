import os,sys,json
from pathlib import Path
import numpy as np
import pytest
@pytest.fixture(scope='module')
def mod():
 root=Path(os.environ.get('GWA_EMBEDDING_CANDIDATE',str(Path(__file__).resolve().parents[1])));sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import local_embeddings
 yield local_embeddings
 sys.path.remove(str(root))
@pytest.fixture(scope='module')
def emb(mod):return mod.LocalEmbeddings(Path(os.environ.get('GWA_EMBEDDING_MODEL',str(Path(__file__).resolve().parents[1]/'data/models/multilingual-minilm'))),Path(os.environ.get('GWA_EMBEDDING_MANIFEST',str(Path(__file__).resolve().parents[1]/'config/embedding-model.json'))))

def test_pinned_identity_and_real_cpu_vectors(emb):
 assert emb.identity=='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211226b894fcb81acc59f3b34ba3efd5f42';v=np.asarray(emb.encode(['formación de jóvenes','apoyo de empresas']));assert v.shape==(2,384) and np.isfinite(v).all();assert np.allclose(np.linalg.norm(v,axis=1),1,atol=1e-5)

def test_no_silent_token_truncation(emb):
 with pytest.raises(ValueError):emb.encode(['formación '*500])

@pytest.mark.parametrize('texts',[[],[''],['a',None],'plain string'])
def test_bad_input_rejected(emb,texts):
 with pytest.raises(ValueError):emb.encode(texts)

def test_changed_weight_manifest_rejected_before_load(mod,tmp_path):
 d=json.loads(Path(os.environ.get('GWA_EMBEDDING_MANIFEST',str(Path(__file__).resolve().parents[1]/'config/embedding-model.json'))).read_text());d['files']['model.safetensors']['sha256']='0'*64;p=tmp_path/'manifest.json';p.write_text(json.dumps(d))
 with pytest.raises(ValueError):mod.LocalEmbeddings(Path(os.environ.get('GWA_EMBEDDING_MODEL',str(Path(__file__).resolve().parents[1]/'data/models/multilingual-minilm'))),p)

def test_unknown_revision_not_silently_selected(mod,tmp_path):
 d=json.loads(Path(os.environ.get('GWA_EMBEDDING_MANIFEST',str(Path(__file__).resolve().parents[1]/'config/embedding-model.json'))).read_text());d['revision']='unknown';p=tmp_path/'manifest.json';p.write_text(json.dumps(d))
 with pytest.raises(ValueError):mod.LocalEmbeddings(Path(os.environ.get('GWA_EMBEDDING_MODEL',str(Path(__file__).resolve().parents[1]/'data/models/multilingual-minilm'))),p)

def test_symlink_model_root_rejected(mod,tmp_path):
 p=tmp_path/'model';p.symlink_to(Path(os.environ.get('GWA_EMBEDDING_MODEL',str(Path(__file__).resolve().parents[1]/'data/models/multilingual-minilm'))),target_is_directory=True)
 with pytest.raises(ValueError):mod.LocalEmbeddings(p,Path(os.environ.get('GWA_EMBEDDING_MANIFEST',str(Path(__file__).resolve().parents[1]/'config/embedding-model.json'))))

def test_manifest_path_escape_rejected(mod,tmp_path):
 d=json.loads(Path(os.environ.get('GWA_EMBEDDING_MANIFEST',str(Path(__file__).resolve().parents[1]/'config/embedding-model.json'))).read_text());d['files']['../escape']={'sha256':'0'*64,'bytes':1};p=tmp_path/'manifest.json';p.write_text(json.dumps(d))
 with pytest.raises(ValueError):mod.LocalEmbeddings(Path(os.environ.get('GWA_EMBEDDING_MODEL',str(Path(__file__).resolve().parents[1]/'data/models/multilingual-minilm'))),p)
