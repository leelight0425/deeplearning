#include"normal.h"

struct node
{
    int data;
    node* next;

};
// node* head;
node* insert(node*head,int x)
{
    
    node*temp=new node;
    temp->data=x;
    temp->next=head;
    head=temp;
    return head;
    

    
}
void Print(node*head)
{
   
   while (head!=nullptr)
   {
    cout<<head->data<<" ";
    head=head->next;
   }
   
}
int main()
{
    node*head=nullptr;
    for (int i = 0; i < 5; i++)
    {
        int x;
        cin>>x;
        cout<<"List after inserting "<<x<<" is: ";
        head=insert(head,x);  
        Print(head);
    }
    
    
    
    
    

}
