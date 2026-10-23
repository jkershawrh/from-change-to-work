export type CameraMode='auto'|'hangar'|'aircraft'|'detail'|'cell'
export const SCENE_ASSET='models/approved-aircraft/scene.glb'
export const CELL_POSITION:[number,number,number]=[9,.85,27]
export function cameraFor(mode:Exclude<CameraMode,'auto'>):{position:[number,number,number];target:[number,number,number]}{
 const poses={hangar:{position:[39,14,56],target:[0,6,1]},aircraft:{position:[26,7,26],target:[12,5.8,4]},detail:{position:[12.7,3,32],target:[9,1.45,26.5]},cell:{position:[11.5,2.6,30.2],target:[9,1.45,26.5]}} as const
 return {position:[...poses[mode].position],target:[...poses[mode].target]}
}
export function automaticCamera(progress:number):Exclude<CameraMode,'auto'>{return progress<.06?'hangar':progress<.42?'detail':'cell'}
export function plateFor(chapter:number,progress:number){return chapter===0?(progress<.12?'01-hangar':'03-robot-cell'):(progress<.3?'02-aircraft-detail':'03-robot-cell')}
