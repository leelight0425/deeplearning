#include"normal.h"
class thisDemo
{
    public:
    int number;
    thisDemo(int number)
    {
        this->number=number;

    }
    thisDemo& operator+ (thisDemo d1)//引用与否的区别
    {
        this->number+=d1.number;
        return *this;

    }
    void null()
    {
        cout<<"number"<<endl;
    }


};
void Null()
{
   thisDemo*p=NULL;
   p->null();



}
int main()
{
   
    thisDemo(20);
    thisDemo(10);
    thisDemo(20)+thisDemo(10);
    


}