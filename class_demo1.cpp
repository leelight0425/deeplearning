#include"normal.h"
class Phone 
{
    public:
    string p_name;
    Phone(string name)
    {
        p_name=name;
    }
};

class Person
{
    public:
    static string name;
    // Phone p_name;
    
};
string Person::name="leelight";
void test01()
{
    Person p1;
    cout<<p1.name<<endl;
}
int main()
{
    test01();
    return 0;
}
扩大飞机咖啡接哦