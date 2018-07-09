import sys
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class emailMessage():

    subject: str
    mailfrom: str
    mailto: str
    htmlbody: str
    sender_name: str = ''
        
    def send( self, mail_server ):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.subject
        if self.sender_name:
            msg['From'] = f'{self.sender_name} <{self.mailfrom}>'
        else:
            msg['From'] = self.mailfrom
        print( msg['From'] )
        msg['To'] = self.mailto
        msg.attach(MIMEText('Open deze mail in een email client die html aan kan.', 'plain', 'utf-8'))
        msg.attach(MIMEText(self.htmlbody, 'html', 'utf-8'))
        mail_server.send( msg['From'], msg['To'], msg )
        
    
class smtpServer(object):
    
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password ):

        self.mailserver = smtplib.SMTP(smtp_server, smtp_port)
        self.mailserver.starttls()
        self.mailserver.login(smtp_user, smtp_password)

    @classmethod # Aanroepen als db = mailClass.from_inifile( 'mail.ini' )
    def from_inifile( cls, inifilename ):
        from configparser  import ConfigParser
        inifile = ConfigParser()
        inifile.read( inifilename )
        params = tuple( inifile.get( 'mail_server', param ) for param in ['smtp_server', 'smtp_port', 'smtp_user', 'smtp_password'])
        return cls( *params )

    def send( self, mailfrom, mailto, msg ):
        self.mailserver.sendmail(mailfrom, mailto, msg.as_string())

    def quit( self ):
        self.mailserver.quit()

        
