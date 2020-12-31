from os import name
from django.http.response import JsonResponse
from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from django.views.generic import CreateView
from django.views.generic.base import TemplateView
from .models import Team_Details
from .response import JSONResponse, response_mimetype
from .forms import Team_Details_form
from .constants import Constant_Data as constants
from logging import Logger
import os,shutil
import pandas
import smtplib,sys,configparser,logging,copy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, datetime
# Create your views here.

message=""
team_name=""

def SendEmail(SMTP_SERVER,PORT,SENDER,Mail_List,SUBJECT,Message):
    """Send Email utility

    Arguments:
        Mail_List {[list]} -- [Email receiver]
        SUBJECT {[string]} -- [Email subject]
        Message {[string]} -- [Email body]
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = Mail_List 
    msg['Body'] = Message
    msg.attach(MIMEText(Message,'html'))
    try:
        smtpObj = smtplib.SMTP(SMTP_SERVER,int(PORT))
        smtpObj.sendmail(SENDER, Mail_List, msg.as_string())
        print ("Successfully sent email")
    except Exception:
        print ("Error: unable to send email")

def get_content(filepath):
    with open(filepath,'r',encoding='utf-8-sig') as bodyfile:
        return bodyfile.readlines()

def notify_santa(child_row,current_row,message,details_dict,teamfolderpath):
    santadetails={}
    santadetails['Name']=current_row.name
    santadetails['Email']= current_row['Email']
    print(santadetails['Name'] +" => "+child_row.index.values[0:1][0])
    message=str(message).format(
        
        santa_name= santadetails['Name'].split(' ')[0],
        child_name=child_row.index.values[0:1][0],
        child_emp_id= child_row['Emp_Id'].values[0:1][0],
     
        contact=child_row['Contact_Number'].values[0:1][0],
        preferred_service_provicer=child_row['Delivery_service'].values[0:1][0],
        wishlist=child_row['Wishlist'].values[0:1][0],
        address=child_row['Address'].values[0:1][0],
        child_email=child_row['Email'].values[0:1][0],
        
        )
    
    smptpserver,port,sender,subject = constants.SMTP_SERVER.value,constants.PORT.value,constants.SENDER.value,constants.SUBJECT.value
    


    teamfolderpath += '\\' +santadetails['Name'].split(' ')[0]+'.html'
    with open(teamfolderpath,'w',encoding="utf-8") as f:
        f.write(message)
    SendEmail(smptpserver,port,sender,santadetails['Email'],subject,message)
    details_dict[santadetails['Name']] = child_row.index.values[0:1][0]

def assign_child(team_members,child_row,current_row):
    counter = 0
    isvalid=False
    while(not isvalid):
        counter+=1
        if(child_row.index.values[0:1][0]== current_row.name):
            child_row= team_members.sample()
            print(f"Trying Again for {current_row.name}")
            continue
        else:
            isvalid=True
            team_members.drop(child_row.index.values[0:1][0], inplace=True)
            break
    return isvalid,child_row,team_members
        
def get_rowdetails(df,team_members,message,teamfolderpath):
    details=[]
    details_dict={} 
    member_list=list(df.index)
    Parent_with_no_child=[]
    Child_with_assigned_parent=[]
    for _, current_row in df.iterrows():
        child_row= team_members.sample()
        isvalid,child_row,team_members = assign_child(team_members,child_row,current_row)
        if(not isvalid):
            details_dict[current_row.name]='NA'
            Parent_with_no_child.append(current_row.name)
            
            print("Sorry, No child is assign for => "+ current_row.name)
            logging.debug("Sorry, No child is assign for => "+ current_row.name)
            continue
        notify_santa(child_row,current_row,message,details_dict,teamfolderpath)
        Child_with_assigned_parent.append(child_row.index.values[0:1][0])
    details.append(details_dict)
    print(Parent_with_no_child, set(member_list) - set(Child_with_assigned_parent))
    return details

def main(filepath,emailbodypath,teamfolderpath):
    try:
        if( not os.path.exists(filepath)):
            message=f"{filepath} does not Exist."
            print(message)
            raise Exception(message)
        df = pandas.read_excel(filepath,header=0,index_col="Name")
        team_members=copy.deepcopy(df)
        
        message=" ".join(get_content(emailbodypath))
        details = get_rowdetails(df,team_members,message,teamfolderpath)
        return details
    except Exception as ex:
        print(ex)


class TeamCreateView(CreateView):
    model = Team_Details
    form_class = Team_Details_form
    template_name='name_assigner/index.html'

    def form_valid(self, form):
        self.object = form.save()
        data = {'status': 'success'}
        response = JSONResponse(data, mimetype=response_mimetype(self.request))
        return response


def file_upload_view(request):
    if request.method=='POST':
        try:
            my_file=request.FILES.get('file')
            teamname= request.POST['teamname']
            teamname = str(teamname).replace(' ','_')
            Team_Details.objects.create(name=teamname,file=my_file)
            # emailbodypath=r'D:\Ravi\secret_santa\name_assigner\static\name_assigner\email_body.html'
            emailbodypath= constants.EMAIL_BODY_PATH.value
            filepath=constants.UPLOADED_FILE_PATH.value+'\\'+my_file.name
            if not os.path.exists(filepath):
                raise Exception("filenames should not contain any spaces")
            teamfolderpath= constants.UPLOADED_FILE_PATH.value+'\\'+teamname
            
            if(not os.path.exists(teamfolderpath)):
                os.makedirs(teamfolderpath)
            teamfilepath=teamfolderpath + '\\'+ my_file.name
            shutil.copy(filepath,teamfilepath)
            os.remove(filepath)
            filepath = teamfilepath
        

            logfile=constants.LOG_FILE_PATH.value
            logging.basicConfig(filename=logfile,level=logging.DEBUG)
            logging.debug( teamname +" => "+ str(datetime.now()))
            details = main(filepath,emailbodypath,teamfolderpath)
            logging.debug(details)
            Team_Details.objects.filter(name=teamname).update(child_details=details)
            if details == None:
                raise Exception("Data is not in proper format.")
            return render(request,'name_assigner/success.html')
            
        except Exception as ex:
            context={
                # 'posts':posts,
                'error':ex
            }
            return render(request,'name_assigner/error.html',context)
        
    return JsonResponse({'Allowed' : 'false'})
    