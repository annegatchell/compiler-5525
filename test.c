#include <stdio.h>
#include <stdlib.h>

int main(int argc, char* argv[]){
	int bigtag = 3;
	int num = 0xdeadbeef;
	printf("%d",(((long)num) & 3) == 0); 
	printf("%x\n", num);
	printf("%lx\n", (long)num);
	printf("%lx\n", (long)num | 3);
	printf("%x\n", &num);
	int test = 0xdeedbaef;
	printf("%x, %lx, %lx \n",&test, (long)&test, (long)&test | 3);
	printf("%lx, %lx\n", (long)&num, (long)&num | 3);
	return 0;
}
