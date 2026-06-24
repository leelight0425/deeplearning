#include"normal.h"
#include<vector>
#include<algorithm>
void MyPrint(int p)
{
    cout<<p<<endl;
}
class Person
{
   
   
    public: 
    int m_Age;
    string m_Name;
    Person(string name,int age)
    {
        m_Name=name;
        m_Age=age;

    }

};
void test01()
{
    vector<Person> v1;
    Person p1("lele",21);
    Person p2("lele",221);
    Person p3("lele",211);
    Person p4("lele",251);
    Person p5("lele",201);
    v1.push_back(p1);
    v1.push_back(p2);
    v1.push_back(p3);
    v1.push_back(p4);
    v1.push_back(p5);
    //访问数组中的元素
    for (vector<Person> ::iterator it  = v1.begin(); it != v1.end(); it++)
    {
        cout<<(*it).m_Age<<endl;
    }
    
//     vector<int>::iterator itBegin=v1.begin();
//     vector<int>::iterator itEnd=v1.end();
//     while (itBegin!=itEnd)
//     {
//         cout<<*itBegin<<endl;
//         itBegin++;
//     }
//     for_each(v1.begin(),v1.end(),MyPrint);
    
}
void test02()
{
    vector<vector<int>> v;
    vector<int>v1;
    vector<int>v2;
    vector<int>v3;
    vector<int>v4;
    for (int i = 0; i < 4; i++)
    {
        v1.push_back(i+1);
        v2.push_back(i+2);
        v3.push_back(i+3);
        v4.push_back(i+4);
    }
    v.push_back(v1);
    v.push_back(v2);
    v.push_back(v3);
    v.push_back(v4);
    for (vector<vector<int>>::iterator it = v.begin(); it != v.end(); it++)
    {
        for(vector<int>::iterator vit=(*it).begin();vit!=(*it).end();vit++)
        {
            cout<<(*vit)<<" ";
        }
        cout<<endl;
    }
    
    
    
}
void test03()
{
    string s1;
  const char * str ="dees";
  str="lee";
    string s2(str);
    string s3(s2);
    string s4;
    s4=(4,'s');
    string s5;
    s5.assign("hello",3);
    cout<<str<<endl;

}
void test04()
{
    string s1="me";
    s1+="like cs";
    s1.append(" and lol",5,3);
    cout<<s1<<endl;
}
void test05()
{
    string s1("leelight");
    int a=s1.find("li");
    s1.replace(3,5,"shiguang");
    cout<<s1<<endl;
}
void test06()
{
    string s1("leelight");
    string s2("leelight");
    if (s1.compare(s2)==0)
    {
        cout<<"not equal"<<endl;
    }
    else
    {
        cout<<"equal"<<endl;
    }
    
    
}

int main()
{
    test06();
}