#include<iostream>
#include<string>
#include<ctime>

#define week 7
 using namespace std;
//  int add (int num1,int num2)
//      {
//       int sum = num1+num2;
//       return sum;
//      }
//   void test1()
//   {
//     cout<<"you are right";
//   }    

// //      int a=add(3,5)
//   void swap1(int *p1,int *p2)
//   {
//     int temp=*p1;
//     *p1=*p2;
//     *p2=temp;




//   }
//   int bubblesort(int *arr,int len)
//   {
//     for (int i = 0; i < len; i++)
//     {
//       for (int j = 0; j < len-1; j++)
//       {
//         if (arr[j]>arr[j+1])
//         {
//          int temp=arr[j];
//          arr[j]=arr[j+1];
//          arr[j+1]=temp;
//         }
        
//       }
      
//     }
//     for (int i = 0; i <len; i++)
//     {
//       cout<<arr[i]<<endl;
//     }
    
//     return *arr;
//   }
  struct student
    {
      string name;
      int age;
      int score;
    };
  struct teacher
  {
    string id;
    string name;
    int age;
    struct student sArray[5];
  };
  
    // void printstedent1(struct student *s)
    // {
    //   cout<<s->name<<endl;
    // }
  teacher tArray[3];
  int len=sizeof(tArray)/sizeof(tArray[0]); 
  
  void  printInfo( teacher tArray[],int len)
  {
    for (int i = 0; i < len; i++)
    {
      string tname="ABC";
      tArray[i].name="teachet-";
      tArray[i].name+=tname[i];
      cout<<tArray[i].name<<endl;
      for (int j = 0; j < 5; j++)
      {
        tArray[i].sArray[j].score=90;
        cout<<tArray[i].sArray[j].score<<endl;
      }
      
    }
    

  }
  int *func()
  {
    int *p=new int(10);
    return p;
  }
  void test1()
  {
    int *p=func();
    cout<<*p<<endl;
    cout<<*p<<endl;
    cout<<*p<<endl;
    delete p;
    cout<<*p<<endl;
    cout<<*p<<endl;
    cout<<*p<<endl;
  }
  void test2()
  {
    int a =10;
    int &b=a;
    b=20;
    cout<<a<<endl;
    void test5();
  }
  int& test3()
  {
    static int a =10;
    return a;
  }
   void test2(int a)
  {
    a =10;
    int &b=a;
    b=20;
    cout<<a<<"$"<<endl;
  }
  class circle
  {
  
  public:
    // circle(/* args */);
    // ~circle();
    int r;
    double zc()
    {
      return 2*3.14*r;
    }
  };
  
 
  class student1
  {
  
  public:
  string name;
  int age;
  void printInfo()
  {
    cout<<"name:"<<name<<"\tage:"<<age<<endl;

  }
   
  };
  class Person
  {
  private:
    string name;
    int age=15;
    string idol;
  public:
    string getName(string printName="l")
    {
      name=printName;
      return name;
    }
    int  getAge()
    {
      return age; 
    }
    void getIdol(string printIdol)
    {
      idol=printIdol;
    }
    Person( Person &p)
    {
      int*p=new int(p.age);
      cout<<"start success!"<<endl;
    }
    ~Person()
    {
      cout<<"start success!"<<endl;
    }  

  };
  void add(int a ,int b)
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
  // Person p1;
  // p1.getIdol("leelight");
  // string p1_name=p1.getName("leelight");
  // cout<<p1.getAge()<<endl;
  // cout<<p1_name<<endl;
  // cout<<"ÀîÊÀ¹â"<<endl;
  // void test4();
  // cout<<p1.getIdol()<<endl;
  // student1 s1;
  // s1.name="leelight";
  // s1.age=25;
  // s1.printInfo();
  // circle c1;
  // c1.r=3;
  // cout<<c1.zc()<<endl;
  // // test1();
  // test2(32);
  // // int &ref=test3();
  // // cout<<ref<<endl;
  // // cout<<ref<<endl;
  // // cout<<ref<<endl;
  
  

  // teacher aArray[2];
  // printInfo(aArray,4);
  //  //  cout<<"hello world"<<endl;
    // system("pause");
    // int a = 10;
    // float f1=3e-2;
    // cout<<"a="<<a<<endl;
    // cout<<"a week have "<<week<<" days"<<endl;
    // cout<<sizeof(long long);
    // cout<<f1<<endl;
    // char ch='a';
    // cout<<int(ch)<<endl;
    // cout<<"\a";
    // string ch1="sddad";
    // cout<<ch<<endl;
    // bool frag = true;
    // cout<<frag<<endl;
    // frag=false;
    // cout<<frag<<endl;
    // cout<<sizeof(bool);
    // string name= "dsafd";
    // int age=0;
    // string sex="dafda";
    // cin>>name;
    // cout<<"your name:"<<name<<endl;    
    // cin>>age;
    // cout<<"your age:"<<age;    
    // cin>>sex;    
    // cout<<"your sex:"<<sex;
   //  int a =1;
   //  ++a;
   //  cout<<"a="<<a;
   // int a=10;
   // int b=10;
   // int c=(a==b);
   // cout<<(a==b)<<endl;
   // int a=10;
   // int b=0;
   // cout<<(b||a)<<endl;
   // int a=10;
   // cout<<"please input your score"<<endl;
   // cin>>a;
   // if (a<600)
   // {
   //    cout<<"very sorry"<<endl;
   //    /* code */
   // }
   // else
   // {
   //   if (a>650)
   //   {
   //    cout<<"peking university"<<endl;
   //    /* code */
   //   }
   //   else
   //   {
   //    cout<<"985 university"<<endl;
   //   }
   // int a=10;
   // int b=5;
   // int c=1;
   
   // if (a>b)
   // {
   //    if (b<c)
   //    {
   //      cout<<"b zui qing"<<endl;
   //    }
   //    else
   //    {
   //       cout<<"c zuiqing"<<endl;
   //    }
      
   // }
   // else
   // {
   //    if (a>c)
   //    {
   //      cout<<"c zui qing";
   //    }
   //    else
   //    {
   //       cout<<"a zuiqing"<<endl;
   //    }
      
      // int a=1;
      // cout<<"please input your score";
      // cin>>a;
      // switch (a)
      // {
      // case 10:
      //    cout<<"perfect"<<endl;
      //    break;
      
      // default:
      //    cout<<"very good"<<endl;
      
      //    break;
      // }
     
      // int num=rand()%100; 
      // int val=0;
      // while (1)
      // {
      //    cin>>val;
      //    if (val<num)
      //    {
      //       cout<<"smaller"<<endl;
      //    }
      //    else if (val>num)
      //    {
      //       cout<<"bigger"<<endl;
      //    }
      //    else
      //    {
      //      cout<<"you are right!"<<endl;
      //      break;
      //    }
         
         
      // }
      // int a=0;
      // while (a<1000)
      // {
      //    int num1=a%10;
      //    int num=a/10;
      //    int num2=num%10;
      //    int num3=a/100;
      //    if (num1*num1*num1+num2*num2*num2+num3*num3*num3==a)
      //    {
      //       cout<<a<<"is shui xian shu"<<endl;
           
      //    }
      //    a++;
         


      // }
      // for(int i=1;i<101;i++){

      //    int num1=i%7;
      //    int num2=i/10%7;
      //    int num3=i%10%7;
      //    if (num1==0)
      //    {
      //       cout<<"qiao zhuo zi"<<endl;
      //    }
      //    else if (num2==0)
      //    {
      //       cout<<"qiao zhuo zi"<<endl;
      //    }
      //    else if (num3==0)
      //    {
      //      cout<<"qiao zhuo zi"<<endl;
      //    }
      //    else
      //    {
      //       cout<<i<<endl;
      //    }
         
         
         
      // }
      //ä¹˜æ³•è¡?
      //  cout<<"99 mutipy table"<<endl;
      // for (int i = 1; i < 10; i++)
      // {
      //    for (int j = 1; j< i+1; j++)
      //    {
      //       cout<<j<<"*"<<i<<"="<<i*j<<"\t";
      //    }
      //    cout<<endl;
      // }
      //100ä»¥å†…çš„å¶æ•?
      // // for (int i = 0; i < 101; i++)
      // // {
         
      // //    if (i%2==0)
      // //    {
      // //       continue;
      // //    }
      // //    cout<<i<<endl;
      // // }
      // int arr[10];
      // cout<<sizeof(arr[0])<<endl;
      // cout<<&arr[9]<<endl;
      // int arr[]={200,342,532,250,259};
      // int start=0;
      // int temp=0;
      // int end=sizeof(arr)/sizeof(arr[0])-1;
      // while (start<end)
      // {
      //   temp=arr[start];
      //   arr[start]=arr[end];
      //   arr[end]=temp;
      //   start++;
      //   end--;


      // }
      // for (int i = 0; i < 5; i++)
      // {
      //   cout<<arr[i]<<endl;
      // }
    //   for (int i = 0; i < 5; i++)
    //   {
    //     for (int j = 0; j <5-i; j++)
    //     {
    //       if (arr[j]>arr[j+1])
    //       {
    //         int temp=0;
    //         temp=arr[j];
    //         arr[j]=arr[j+1];
    //         arr[j+1]=temp;

          
    //       }
          
    //     }
        
    //   }
    //  for (int i = 0; i <5; i++)
    //  {
    //   cout<<arr[i]<<endl;
    //  }
    //  int a=add(3,6);
    //  cout << a<<endl;
    //  test1();
    // 
    // int a =10;
    // int *p;
    // p=&a;
    // cout<<p<<endl;
    // *p=1000;
    // cout<<a<<endl;
    // cout<<sizeof(p)<<endl;
    // int a=10;
    // int b=20;
    // // int * const p=&a;
    // // *p=20;
    // // p=&b;

    // // int arr[]={1,2,3,4,5,6,7,8,9,0};
    // // int *p=arr;
    // // for (int i = 0; i <10; i++)
    // // {
    // //   cout<<*p<<endl;
    // //   p++;
    // // }
    // swap1(&a,&b);
    // cout<<a<<endl;
    // int arr[]={2,1,0,9,7,5,6,3,4,5,10};
    // int len1=sizeof(arr)/sizeof(arr[0]);
    // bubblesort(arr,len1);
    
    
    // student arr[2]={{"zhang",32,23},
    // {"lee",21,39}};
    // // cout<<arr[1].name<<endl;
    // student *p =arr;
    // // cout<<p->age<<endl;
    // struct teacher  
    // {
    //   string name;
    //   int age;
    //   int socer;
    //   struct student s1;
      
    // };
    // struct student s1;
    
    // teacher t;
    
  //  teacher t[3];
  //  static int a=10;
   system("pause");

    return 0;



 }