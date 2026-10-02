"""Compare deterministic verification metrics across two complete Vision builds."""
import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'output'/'VEH_DeLorean_Vision'/'work'
rep=json.loads((root/'projects'/'VEH_DeLorean_Vision'/'report.json').read_text())
keys=['objects','tris','dims','bbox_min','hygiene','uv_overlap','texel','uv','lod_tris','engine']
summary={stage:{key:data['metrics'][key] for key in keys if key in data['metrics']} for stage,data in rep['stages'].items()}
summary['inputs']={stage:data['inputs_hash'] for stage,data in rep['stages'].items()}
summary['gate']={stage:data['summary'] for stage,data in rep['stages'].items()}
base=out/'rebuild_baseline.json'
if '--snapshot' in sys.argv:
 assert all(v['result']=='PASS' for v in summary['gate'].values()),'Baseline gates must pass'
 base.write_text(json.dumps(summary,indent=2));print('Baseline saved')
else:
 old=json.loads(base.read_text());same=old==summary
 result={'result':'PASS' if same else 'FAIL','identical_stage_metrics':same,'stages':summary['gate'],'metrics':summary}
 (out/'clean_rebuild.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({'result':result['result'],'identical_stage_metrics':same,'tris':[summary[str(k)].get('tris',summary[str(k)].get('lod_tris')) for k in range(1,5)]}))
 assert same,'Rebuild metrics changed'
