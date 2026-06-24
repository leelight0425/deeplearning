#include"student.h"

  void student1::printInfo()
  {
    cout<<"name:"<<name<<"\tage:"<<age<<endl;

  }
   
    string Person::getName(string printName)
    {
      name=printName;
      return name;
    }
    int  Person::getAge()
    {
      return age; 
    }
    void Person::getIdol(string printIdol)
    {
      idol=printIdol;
    }
    int main ()
 {
  Person p1;
  p1.getIdol("leelight");
  string p1_name=p1.getName("leelight");
  cout<<p1.getAge()<<endl;
  cout<<p1_name<<endl;system("pause");
    return 0;

 }

