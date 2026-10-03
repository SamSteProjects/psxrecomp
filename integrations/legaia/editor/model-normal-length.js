// Exact integer rounding for existing signed source normal coordinates.
export function rescaleStoredNormal(vector,length){
  if(!Number.isSafeInteger(length)||length<1||length>32767||!Array.isArray(vector)||vector.length!==3||vector.some(v=>!Number.isSafeInteger(v)||v< -32768||v>32767))throw new Error('Normal rescaling requires signed source XYZ and integer length1..32767.');
  const squared=vector.reduce((sum,v)=>sum+BigInt(v)*BigInt(v),0n);
  if(squared===0n)return [0,0,0];
  return vector.map(value=>{
    const product=BigInt(Math.abs(value))*BigInt(length),square=product*product;
    let low=0n,high=BigInt(length)+1n;
    while(high-low>1n){const middle=(low+high)/2n;if(middle*middle*squared<=square)low=middle;else high=middle;}
    if(4n*square>=squared*(2n*low+1n)**2n)low++;
    return Number(value<0?-low:low);
  });
}
