#include"normal.h"
void add(int &a ,int &b)
  {
    a=10;
    b=20;
    cout<<a<<endl;
    cout<<b<<endl;
  }
  
  
 int main ()
 {
  int a=1;
  int b=2;
  add(a,b);
  cout<<a<<endl;
  cout<<b<<endl;
 }