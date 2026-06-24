
//学习如何扭曲图像，来扫描文档
#include<opencv2/imgcodecs.hpp>
#include<opencv2/highgui.hpp>
#include<opencv2/imgproc.hpp>
#include<iostream>

using namespace std;
using namespace cv;

/// <summary>
/// Warp Images
/// </summary>
float w = 250, h = 350;//图片大小
mat matrix, imgwarp;
void main() {
	//图片用画图打开，在屏幕左下角会显示点的坐标
	string path = "resources/cards.jpg";
	mat img=imread(path);//matrix data type 由opencv引入来处理图像
	point2f src[4] = { {529,142},{771,190},{405,395},{674,457} };//point2f表示浮点数
	point2f dst[4] = { {0.0f,0.0f},{w,0.0f},{0.0f,h},{w,h} };//point2f表示浮点数

	matrix = getperspectivetransform(src, dst);
	warpperspective(img, imgwarp, matrix, point(w,h));
	
	//确定src坐标是否正确
	for (int i = 0; i < 4; i++) {
		circle(img, src[i], 10, scalar(0, 0, 255), filled);
	}

	imshow("image", img);
	imshow("image warp", imgwarp);
	waitkey(0);//增加延时，0表示无穷
}
