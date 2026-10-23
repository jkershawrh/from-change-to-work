import {visualContext} from './narrative'
export default function VisualContext({chapter}:{chapter:number}){const v=visualContext[chapter];return <aside className="cine-visual-context" aria-label="Visual title, input and outcome"><h2>{v.title}</h2><dl><div><dt>INPUT</dt><dd>{v.input}</dd></div><div><dt>OUTCOME</dt><dd>{v.output}</dd></div></dl></aside>}
