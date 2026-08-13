export type User={id:string;email:string;name:string|null};
export type Campaign={id:string;name:string;subject:string;body:string;source:string;status:string;scheduled_at:string;total_count:number;sent_count:number;replied_count:number;failed_count:number;created_at:string};
export type Recipient={id:string;email:string;first_name:string|null;last_name:string|null;company:string|null;status:string;current_step:number;last_sent_at:string|null;replied_at:string|null;error:string|null};
export type CampaignDetail=Campaign&{recipients:Recipient[];followups:{id:string;position:number;delay_days:number;subject:string|null;body:string}[]};

export async function api<T>(path:string,init?:RequestInit):Promise<T>{
  const response=await fetch(`/backend/api/v1${path}`,{credentials:'include',...init,headers:{...(init?.body instanceof FormData?{}:{'content-type':'application/json'}),...init?.headers}});
  if(!response.ok){const body=await response.json().catch(()=>({detail:'Something went wrong'}));throw new Error(body.detail||body.error||'Something went wrong');}
  if(response.status===204)return undefined as T;
  return response.json();
}

export function statusTone(status:string){
  if(['COMPLETED','REPLIED'].includes(status))return 'green';
  if(['RUNNING','SCHEDULED','ACTIVE'].includes(status))return 'blue';
  if(['FAILED'].includes(status))return 'red';
  if(['PAUSED'].includes(status))return 'amber';
  return 'gray';
}
