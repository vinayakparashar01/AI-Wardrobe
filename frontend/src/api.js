const API_BASE=import.meta.env.VITE_API_BASE||"http://127.0.0.1:8000";
async function request(path,options={}){const token=localStorage.getItem("access_token");const headers={...(options.headers||{})};if(token)headers.Authorization=`Bearer ${token}`;if(options.body&&!(options.body instanceof FormData)&&!headers["Content-Type"])headers["Content-Type"]="application/json";const r=await fetch(`${API_BASE}${path}`,{...options,headers});if(!r.ok){let m=`Request failed (${r.status})`;try{const d=await r.json();m=d.detail||m}catch{}throw new Error(m)}if(r.status===204)return null;return r.json()}
export const api={
login(email,password){return request("/auth/login",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({username:email,password})})},
register(p){return request("/user/",{method:"POST",body:JSON.stringify({name:p.name,username:p.username||p.name,email:p.email,password:p.password})})},
me(){return request("/user/me")},listClothes(){return request("/clothing-items/")},getClothing(id){return request(`/clothing-items/${id}`)},
createClothing(p){return request("/clothing-items/",{method:"POST",body:JSON.stringify(p)})},updateClothing(id,p){return request(`/clothing-items/${id}`,{method:"PUT",body:JSON.stringify(p)})},deleteClothing(id){return request(`/clothing-items/${id}`,{method:"DELETE"})},
listOutfits(){return request("/outfits/")},getOutfit(id){return request(`/outfits/${id}`)},createOutfit(p){return request("/outfits/",{method:"POST",body:JSON.stringify(p)})},updateOutfit(id,p){return request(`/outfits/${id}`,{method:"PUT",body:JSON.stringify(p)})},deleteOutfit(id){return request(`/outfits/${id}`,{method:"DELETE"})}
};
