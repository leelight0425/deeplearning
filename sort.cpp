#include<iostream>
#include<ctime>
#include<string>
using namespace std;
struct hero
{
    string name;
    int age;
};
 void sortHero( hero heroarray[],int len)
    {
        for (int i = 0; i < len-1; i++)
        {
            for (int j = 0; j < len-1-i; j++)
            {
                if (heroarray[i].age>heroarray[i].age)
            
                {
                    hero temp=heroarray[i];
                    heroarray[i]=heroarray[i+1];
                    heroarray[i+1]=  temp;
                }
                
            }
            
        }
    }
void printhero( hero heroarray[],int len)
    {
    for (int i = 0; i < len; i++)
        {
        cout<<"name"<<heroarray[i].name<<"age"<<heroarray[i].age<<endl;
        }
    
    }

int main()
{
   hero heroarray1[]= {{"lee",24},{"light",25}};
   int len=sizeof(heroarray1)/sizeof(heroarray1[0]);
   sortHero(heroarray1,len);
   printhero(heroarray1,len);   
    
   system("pause");
    return 0;
}

    







    
