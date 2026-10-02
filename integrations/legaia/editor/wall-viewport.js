import {wallRectangle} from './collision-rectangle.js';

// Source MAP coordinates use (low, high] for X and [low, high) for Z.
// This is a reference plane; it does not infer terrain or runtime collision.
export function wallCellAt(point){
  if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.z)||point.x<=0||point.x>16384||point.z<0||point.z>=16256)return null;
  const column=Math.max(1,Math.ceil(point.x/128))-1,row=Math.floor(point.z/128)+1;
  const quadrant=(Math.max(1,Math.ceil(point.x/64))-1)%2+2*(Math.floor(point.z/64)%2);
  return {row,column,quadrant};
}

function validateCell(cell){
  if(!cell||!Number.isSafeInteger(cell.row)||cell.row<1||cell.row>127||!Number.isSafeInteger(cell.column)||cell.column<0||cell.column>127||!Number.isInteger(cell.quadrant)||cell.quadrant<0||cell.quadrant>3)throw new Error('Invalid source wall cell');
}

export function wallDragRectangle(startCell,endCell,{quadrant='all',blocked=true}={}){
  validateCell(startCell);validateCell(endCell);
  return wallRectangle({
    row_start:Math.min(startCell.row,endCell.row),row_end:Math.max(startCell.row,endCell.row),
    column_start:Math.min(startCell.column,endCell.column),column_end:Math.max(startCell.column,endCell.column),
    quadrant,blocked,
  });
}

export function wallSelectionGeometry(value){
  const rectangle=wallRectangle(value);
  return {x_min:rectangle.column_start*128,x_max:(rectangle.column_end+1)*128,
    z_min:(rectangle.row_start-1)*128,z_max:rectangle.row_end*128};
}
