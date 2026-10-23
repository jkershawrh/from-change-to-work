import {describe,it,expect} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import {PilotRoadmap} from './PilotRoadmap'
describe('pilot roadmap evidence boundaries',()=>{
 it('shows starting metrics as unmeasured and keeps targets owner agreed',()=>{
  const html=renderToStaticMarkup(<PilotRoadmap/>);
  expect(html).toContain('Starting metrics');expect(html.match(/Not measured/g)).toHaveLength(6)
  expect(html).toContain('Agree after baseline');expect(html).toContain('No savings or performance improvement claimed')
 })
 it('separates historical simulator proof from future hardware and production gates',()=>{
  const html=renderToStaticMarkup(<PilotRoadmap/>);
  for(const text of ['Retained simulator evidence','Qualify named compute hosts','Connect one reviewed robot profile','Measure a controlled pilot','Repeat with a second module','TDD','EDD','CDD','BDD','CBT'])expect(html).toContain(text)
  expect(html).toContain('Physical motion requires separate authorization');expect(html).toContain('Standards interoperability is pending')
 })
})
