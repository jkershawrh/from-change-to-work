#!/usr/bin/env python3
"""Dependency-free preflight; works before setup, never changes the host."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.readiness import collect,write_report
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path);args=ap.parse_args();report=collect()
 if args.out:write_report(args.out,report)
 print(json.dumps(report,indent=2));sys.exit(0 if report['simulation_prerequisites']=='READY' else 2)
