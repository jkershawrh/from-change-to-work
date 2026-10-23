/** Local GLB geometry conversion. Does not execute model scripts or contact a robot. */
import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import {resolve} from 'node:path';
const require=createRequire(resolve('tools/aircraft-assets/package.json'));
const {NodeIO}=await import(pathToFileURL(require.resolve('@gltf-transform/core')));
const {ALL_EXTENSIONS}=await import(pathToFileURL(require.resolve('@gltf-transform/extensions')));
const {MeshoptDecoder}=await import(pathToFileURL(require.resolve('meshoptimizer')));
const draco3d=require('draco3d');
const [input,output]=process.argv.slice(2);if(!input||!output)throw Error('Usage: node scripts/visuals/decode_aircraft.mjs input.glb output.glb');
await MeshoptDecoder.ready;const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'draco3d.decoder':await draco3d.createDecoderModule()});const doc=await io.read(resolve(input));for(const e of doc.getRoot().listExtensionsUsed())if(['EXT_meshopt_compression','KHR_draco_mesh_compression'].includes(e.extensionName))e.dispose();await io.write(resolve(output),doc);console.log('Decoded aircraft geometry; texture/material data retained.');
