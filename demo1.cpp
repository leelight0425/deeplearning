#include"normal.h"
template<class T>
class Base
{

    T m;
};
class son:public Base<>
{

};
void tes01()
{
    son s1;
}