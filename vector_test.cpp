#include"normal.h"
#include<vector>

void print(vector<int>&v1)
{
    for (vector<int>::iterator it= v1.begin(); it != v1.end(); it++)
    {
        cout<<*it<<endl;
    }
}
void test01()
{
    vector<int>v1;
    for (int i = 0; i < 5; i++)
    {
        v1.push_back(i);
    }
    vector<int>v2=v1;
    print(v2);
    vector<int>v3;
    v3.assign(10,100);
    print(v3);
    vector<int>v4;
    v1.insert(v1.begin()+2,10,120);
    print(v1);
    vector<int>(v1);

    
}

int main(){
    test01();
   
}