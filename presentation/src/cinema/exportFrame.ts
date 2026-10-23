/** Reject a stale WebGL scene before painting any new chapter typography. */
export function exportFrameReady(chapter:number,renderedChapter:string|undefined){return chapter!==2&&chapter!==3||renderedChapter===String(chapter)}
