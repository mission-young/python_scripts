#!/usr/bin/python3
import sys
import json
import os

class tovar():
    """重定向python的输出至变量

    print()函数实际上是 sys.stdout 函数，默认输出到终端。
    这里将print()函数重定向到变量

    Attributes:
        str: 用于存储print函数输出的结果
    """
    def __init__(self):
        """
        初始化函数，必备函数
        """
        self.str=''
    def write(self,s):
        """
        将print的值暂存到str，如果多次print，则值会累加，必备函数
        """
        self.str+=s
    def flush(self):
        """
        清空str，必备函数
        """
        self.str=''
    def content(self):
        """
        返回str，将暂存的输出返回到变量中
        """
        return self.str.rstrip()


def writecode(s,mode='update'):
    """
    update模式时，为累加模式
    recreate模式时，重写模式
    """
    if mode == 'recreate':
        w='w'
    else:
        w='a'
    fout = open('tmp.py',w,encoding='utf8')
    fout.write(s)
    fout.close()
# 获得要转化的jupyter文件
filename=sys.argv[1]

# jupyter文件格式实际上是json格式，选择自带的json库来读取，读取后关闭文件
file=open(filename)
data=json.load(file)
file.close()

cells=data['cells']
# 命令单元格的id，必须设置，否则不会显示执行结果
id=1

# term暂存，为输出到终端，随后将print重定向到变量var
var=tovar()
term=sys.stdout
sys.stdout=var


for cell in cells:
    cell_type=cell['cell_type']
    # 单元格为markdown时，不需要处理，打开jupyter文件会自动转换
    if cell_type=='markdown':
        continue
    else:
        # 当jupyter清空了所有输出时，execution_count为null，如果不设置id的话，即使
        # 有执行结果，在jupyter中也不会显示。
        cell['execution_count']=id
        # 将print重定向到终端，以便在终端输出进度，随后重定向到变量
        sys.stdout=term
        print('process: %d/%d' %(id,len(cells)-1))
        sys.stdout=var
        id+=1

        codes=cell['source']
        #新建代码单元格存储文件
        writecode('','recreate')

        for code in codes:
            # 修正jupyter中一些magic code
            if 'matplotlib inline' in code:
                code='import matplotlib.pyplot as plt\n'
            # 逐行写入code cell的代码到文件中
            writecode(code)
        # 执行代码单元格代码，这种形式执行的好处在于，等价于直接把代码拷贝到主程序中，
        # 程序变量等信息保留。由于此时print重定向到tovar函数的str变量中，并不会在终端输出信息。
        exec(open('tmp.py').read())
        # 获取代码运行的结果
        result=var.content()
        # 清空缓存，以便于存储下一次结果
        var.flush()
        # 代码运行为空跳过
        if(result.strip()!=''):
            # 这一点用来判定原jupyter是否有输出，如果没有输出，则需要新建dict，否则只需要替换
            # 相应部分既可以。
            if len(cell['outputs'])==0:
                out={}
                out['name']='stdout'
                out['output_type']='stream'
                out['text']=[res + '\n' for res in result.split('\n')]
                cell['outputs'].append(out)
            else:
                cell['outputs'][0]['name']='stdout'
                cell['outputs'][0]['output_type']='stream'
                cell['outputs'][0]['text']=[res + '\n' for res in result.split('\n')]
            # 在终端中输出
            sys.stdout=term
            print(result)
    # 每运行一次code cell，修改jupyter文件
    file=open(filename,'w')
    json.dump(data,file)
    file.close()
