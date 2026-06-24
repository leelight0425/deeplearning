#include"normal.h"
class building
{
    friend void GoodGay(building build);
    public:
    string m_sittingroom;
    building()
    {
        m_bedroom="ÎÒÊÇ";
        m_sittingroom="¿ÍÌü";
    }
    private:
    string m_bedroom;
};
 
void GoodGay(building build)
{
  cout<<build.m_sittingroom<<endl;
  cout<<build.m_bedroom<<endl;
}
int main()
{
    building build;
    GoodGay(build);
}