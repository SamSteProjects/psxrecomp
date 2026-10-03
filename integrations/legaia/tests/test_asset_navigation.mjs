import assert from 'node:assert/strict';
import {mountAssetNavigation} from '../editor/asset-navigation.js';
const doc={activeElement:null};
class Node{
  constructor(tag){this.tagName=tag;this.ownerDocument=doc;this.children=[];this.dataset={};this.attributes={};this.events=new Map();this.disabled=false;this.tabIndex=0;this.scrolls=0;}
  append(...children){for(const child of children){child.parent=this;this.children.push(child);}}
  contains(node){return node===this||this.children.some(child=>child.contains(node));}
  querySelectorAll(){return this.children.flatMap(child=>child.tagName==='button'?[child]:child.querySelectorAll());}
  setAttribute(key,value){this.attributes[key]=value;}
  addEventListener(key,fn){this.events.set(key,fn);}removeEventListener(key){this.events.delete(key);}
  focus(){doc.activeElement=this;for(let node=this;node;node=node.parent)node.events.get('focusin')?.({target:this});}
  scrollIntoView(){this.scrolls++;}
}
const list=new Node('div'),search=new Node('input');doc.activeElement=search;
let context=['project','scene','active'],page=0,opened=0,paged=0;
const fill=(keys,disabled=false)=>{list.children=[];for(const key of keys){const row=new Node('div');row.dataset.assetKey=key;for(const action of ['open','details']){const button=new Node('button');button.dataset.assetAction=action;button.disabled=disabled;button.onclick=()=>opened++;row.append(button);}list.append(row);}};
fill(['a','b','c']);
let navigation=mountAssetNavigation(list,()=>context,delta=>{if(page+delta<0||page+delta>1)return false;const before=navigation.beforeRender();page+=delta;paged++;fill(page?['d','e']:['a','b','c']);navigation.afterRender(before);return true;});
const key=(name,extra={})=>{const event={target:doc.activeElement,key:name,prevented:false,preventDefault(){this.prevented=true;},...extra};list.events.get('keydown')?.(event);return event;};
const at=(row,action=0)=>list.children[row].children[action];
const tabs=()=>list.querySelectorAll().filter(button=>button.tabIndex===0);
assert.equal(doc.activeElement,search);assert.deepEqual(tabs(),[at(0)]);assert.equal(list.tabIndex,-1);
at(0).focus();key('ArrowDown');assert.equal(doc.activeElement,at(1));key('ArrowRight');assert.equal(doc.activeElement,at(1,1));key('ArrowDown');assert.equal(doc.activeElement,at(2,1));key('Home');assert.equal(doc.activeElement,at(0,1));key('End');assert.equal(doc.activeElement,at(2,1));key('ArrowRight');assert.equal(doc.activeElement,at(2,1));assert.equal(opened,0);assert.deepEqual(tabs(),[at(2,1)]);
for(const name of ['Enter',' ','Tab'])assert.equal(key(name).prevented,false);for(const modifier of ['altKey','ctrlKey','metaKey','shiftKey'])assert.equal(key('Home',{[modifier]:true}).prevented,false);assert.equal(doc.activeElement,at(2,1));
let before=navigation.beforeRender();fill(['a','b','c']);navigation.afterRender(before);assert.equal(doc.activeElement,at(2,1));
before=navigation.beforeRender();fill(['a','b','c'],true);navigation.afterRender(before);assert.equal(doc.activeElement,list);assert.equal(tabs().length,0);before=navigation.beforeRender();fill(['a','b','c']);navigation.afterRender(before);assert.equal(doc.activeElement,at(2,1),'Busy controls retain the stable asset/action for restoration.');
assert.equal(key('PageDown').prevented,true);assert.equal(page,1);assert.equal(doc.activeElement,at(0,1));assert.equal(key('PageDown').prevented,false);assert.equal(key('PageUp').prevented,true);assert.equal(doc.activeElement,at(2,1));assert.equal(paged,2);assert.equal(opened,0);
search.focus();before=navigation.beforeRender();fill(['c']);navigation.afterRender(before);assert.equal(doc.activeElement,search);assert.deepEqual(tabs(),[at(0,1)]);
at(0,1).focus();before=navigation.beforeRender();fill([]);navigation.afterRender(before);assert.equal(doc.activeElement,list);assert.equal(list.tabIndex,0);before=navigation.beforeRender();fill(['a']);navigation.afterRender(before);assert.equal(doc.activeElement,at(0));
at(0,1).focus();before=navigation.beforeRender();context=['different-project','scene','active'];fill(['a']);navigation.afterRender(before);assert.notEqual(doc.activeElement,at(0,1));assert.deepEqual(tabs(),[at(0)]);
at(0,1).focus();context=['third-project','scene','active'];before=navigation.beforeRender();fill(['a']);navigation.afterRender(before);assert.notEqual(doc.activeElement,at(0,1),'Capture the rendered scope even when new state arrives before rebuilding.');assert.deepEqual(tabs(),[at(0)]);
at(0).focus();doc.activeElement.onclick();assert.equal(opened,1);navigation.dispose();assert.equal(list.events.size,0);
console.log('Asset navigation: two-action cards, focus-only arrows, native activation, stable redraw/busy focus, result paging, search/empty/context boundaries and disposal passed.');
