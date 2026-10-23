import {plateFor} from './approvedScene'
export const plateNames=['01-hangar','02-aircraft-detail','03-robot-cell'] as const
export type PlateImages=Map<string,HTMLImageElement>
let pending:Promise<PlateImages>|undefined
export function loadPlates(){return pending??=Promise.all(plateNames.map(async name=>{const image=new Image();image.src=import.meta.env.BASE_URL+'review/aircraft-01/'+name+'.png';await image.decode();return [name,image] as const})).then(entries=>new Map(entries))}
/** Synchronous scene selection from decoded assets: never reads a stale React canvas. */
export function drawPlate(c:CanvasRenderingContext2D,images:PlateImages,chapter:number,progress:number,x:number,y:number,width:number,height:number,reduced=false){const image=images.get(plateFor(chapter,progress));if(!image)throw Error('Decoded scene image required');const zoom=reduced?1:1.015+Math.sin(progress*Math.PI)*.035;const scale=Math.max(width/image.width,height/image.height)*zoom,w=image.width*scale,h=image.height*scale;c.save();c.beginPath();c.rect(x,y,width,height);c.clip();c.drawImage(image,x+(width-w)/2,y+(height-h)/2,w,h);c.restore()}
