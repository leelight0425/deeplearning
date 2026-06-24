#pragma once
#include<iostream>
using namespace std;
class student1
  {
  
  public:
  string name;
  int age;
  void printInfo();
//   {
//     cout<<"name:"<<name<<"\tage:"<<age<<endl;

//   }
   
  };
  class Person
  {
  private:
    string name;
    int age=15;
    string idol;
  public:
    string getName(string printName="l");
    // {
    //   name=printName;
    //   return name;
    // }
    int  getAge();
    // {
    //   return age; 
    // }
    void getIdol(string printIdol);
    // {
    //   idol=printIdol;
    // }

  };