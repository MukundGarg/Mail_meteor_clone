import type {Metadata} from 'next';
import './globals.css';
import './contact.css';

export const metadata:Metadata={
  title:'MailPilot — Gmail campaigns made simple',
  description:'Import contacts, personalize Gmail campaigns, schedule follow-ups, and stop automatically on reply.'
};

export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body>{children}</body></html>;
}
