#include <stdio.h>
#include <string.h>



int main() {
    // // printf("Hello, World!\n");
    // // char arr[]="ddsae";
    // // int a= 10;
    // // printf("%s\n",arr);
    // // int len= strlen(arr);
    // // printf("%d\n",len);
    // // return 0;

    // // printf("abc\tda\n");
    // // printf("%lf\n",'\130');
    // // printf("%c\n",'\x60');
    // // printf("%d\n",'\x60');
    // int input=1

    // pri("要不要好好学习/n");
    // scanf("%d",&input);
    // if (input==0)
    // {
    //     printf("找到一个好工作");
        
    //     /* code */
    // }
    // else
    // {
    //     printf("回家种地");
    // }
    // int line = 0;
    // while (line<20000)
    // {
    //     /* code */
    //     printf("come on !%d\n",line);
    //     line++;

    // }
    // if (line>20000)
    // {
    //     printf("thanks");
    // }
    
    // else
    // {
    //   printf("try!");  
    // }
    int radius = 1; // 3x3 核
for (int y = radius; y < height - radius; y++) {
    for (int x = radius; x < width - radius; x++) {
        float sum = 0.0f;
        for (int dy = -radius; dy <= radius; dy++) {
            for (int dx = -radius; dx <= radius; dx++) {
                sum += input[(y+dy)*stride + (x+dx)];
            }
        }
        output[y*stride + x] = sum / 9.0f; // 均值滤波
    }
}
    
    return 0;
} 