import {describe,it,expect,vi} from 'vitest'
import {render,screen,fireEvent,cleanup} from '@testing-library/react'
import {afterEach} from 'vitest'
import TitleScreen from './TitleScreen'
const brand={primary:{name:'Red Hat',logo:'/logos/redhat.svg',alt:'Red Hat'},partner:{name:'Intel',logo:'/logos/intel.png',alt:'Intel'},attribution:'Red Hat × Intel'}
afterEach(cleanup)
describe('opening title',()=>{
 it('introduces the remote-to-robot premise before the first act',()=>{render(<TitleScreen duration={326.45} ready brand={brand} onPlay={()=>{}} onPresent={()=>{}}/>);expect(screen.getByRole('heading',{level:1})).toHaveTextContent('FROM CHANGE');expect(screen.getByText(/Deliver an approved task from remote engineering/)).toBeVisible();expect(screen.getByRole('list')).toHaveTextContent('WORK LOCALLY')})
 it('waits for audio readiness and uses the existing story/presenter entry points',()=>{const play=vi.fn(),present=vi.fn();const {rerender}=render(<TitleScreen duration={326.45} ready={false} brand={brand} onPlay={play} onPresent={present}/>);expect(screen.getByRole('button',{name:/Watch the narrated story/})).toBeDisabled();fireEvent.click(screen.getByRole('button',{name:/Presenter-paced tour/}));expect(present).toHaveBeenCalledOnce();rerender(<TitleScreen duration={326.45} ready brand={brand} onPlay={play} onPresent={present}/>);fireEvent.click(screen.getByRole('button',{name:/Watch the narrated story/}));expect(play).toHaveBeenCalledOnce()})
 it('announces the title before entering the story',()=>{vi.spyOn(HTMLMediaElement.prototype,'play').mockResolvedValue();vi.spyOn(HTMLMediaElement.prototype,'pause').mockImplementation(()=>{});const play=vi.fn();const {container,unmount}=render(<TitleScreen duration={326.45} ready brand={brand} announcementSrc="/opening.wav" onPlay={play} onPresent={()=>{}}/>);fireEvent.click(screen.getByRole('button',{name:/Watch the narrated story/}));expect(play).not.toHaveBeenCalled();expect(screen.getByRole('button',{name:/Opening announcement/})).toBeDisabled();fireEvent.ended(container.querySelector('audio')!);expect(play).toHaveBeenCalledOnce();unmount();vi.restoreAllMocks()})

})
