import {useEffect,useRef,useState} from 'react'
import {Play,BookOpen,ArrowRight} from 'lucide-react'
import {BrandLockup} from '../components/BrandLockup'
import type {BrandConfig} from '../types'
import {seconds} from './model'
import './title-screen.css'
export default function TitleScreen({duration,ready,brand,onPlay,onPresent,announcementSrc}:{duration:number;ready:boolean;brand:BrandConfig;onPlay:()=>void;onPresent:()=>void;announcementSrc?:string}){const audio=useRef<HTMLAudioElement>(null),[announcing,setAnnouncing]=useState(false),[error,setError]=useState('');useEffect(()=>{const player=audio.current;return()=>player?.pause()},[]);async function begin(){if(!announcementSrc){onPlay();return}setError('');setAnnouncing(true);try{await audio.current!.play()}catch{setAnnouncing(false);setError('The opening audio could not play. Please try again.')}}return <section className="cine-title-screen" aria-label="Opening title">
 {announcementSrc&&<audio ref={audio} data-opening-announcement src={announcementSrc} preload="auto" onEnded={()=>{setAnnouncing(false);onPlay()}}/>}
 <img className="cine-title-art" src={import.meta.env.BASE_URL+'review/aircraft-01/01-hangar.png'} alt="Approved C-17 aircraft in an aerospace hangar; illustrative CGI."/>
 <div className="cine-title-shade"/>
 <header><span>EDGE CAPABILITY DELIVERY</span><BrandLockup brand={brand}/></header>
 <div className="cine-title-content"><p className="cine-title-kicker">AN AEROSPACE MANUFACTURING STORY</p><h1>FROM CHANGE<br/>TO <em>WORK.</em></h1><p className="cine-title-premise">Deliver an approved task from remote engineering to the robot cell.<br/><strong>Keep control local.</strong></p>
 <ol className="cine-title-route"><li><span>01</span> APPROVE THE TASK</li><li><span>02</span> DELIVER THE CHANGE</li><li><span>03</span> WORK LOCALLY</li></ol>
 <div className="cine-title-actions"><button className="cine-title-play" disabled={!ready||announcing} onClick={()=>void begin()}><Play size={20}/> {announcing?'Opening announcement…':'Watch the narrated story'} <span>{duration?seconds(duration):'Preparing…'}</span><ArrowRight size={18}/></button><button onClick={()=>{audio.current?.pause();onPresent()}}><BookOpen size={17}/> Presenter-paced tour</button></div>{error&&<p role="alert">{error}</p>}</div>
 <footer><span>INTERACTIVE STORY / RETAINED SIMULATOR PROOF</span><small>Aircraft: pilotcandle5470 / CC BY 4.0 · adapted<br/>Illustrative scenery · physical motion disabled</small></footer>
 </section>}
