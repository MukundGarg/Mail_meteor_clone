import { getSessionUserId } from './session';
import { one } from './db';
export async function currentUser(){const id=await getSessionUserId();if(!id)return null;return one<{id:string,email:string,name:string|null}>('SELECT id,email,name FROM users WHERE id=$1',[id]);}
