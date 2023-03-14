"""gpt memories localization storage, LS memories control, commands auto-runner, network plugins support"""
import json
import os
import re
import subprocess
import threading
import time

import openai
import tiktoken
from simtext import similarity

openai.api_key = ""
sim = similarity()
mem = []
cache = ""
inputLOCK = True
mem_filename = "Elysia.txt"
name = "爱莉希雅"

plugins = [
    '在cmd执行"python gettime.py"可获取当前时间和日期.',
    '在cmd执行"python weather.py"可获取今天天气数据.',
    '在cmd执行"python baike.py {要查询的内容}"可使用百度百科查询内容定义.',
    '在cmd执行"python google.py {要查询的内容}"可使用谷歌查询有关信息.(无特殊要求优先使用谷歌查询)'
]

temporary_prompts = f'''
(命令行打开的默认目录为"{os.path.dirname(__file__)}",
主程序文件名为"{os.path.basename(__file__)}",
记忆数据文件名为"{mem_filename}",
对话中不要提示多余操作.用Markdown语法让你的文字突出重点.
短时间内不要多次调用同一接口程序.
使用shutdown命令请至少延时一分钟且不要主动取消.
如无特别要求,让你帮忙的时候请给出用双引号括起来的CMD命令,
想要执行的CMD命令也需要用双引号括起来,
不要模拟命令输出,不要建议我取消刚刚的指令.
不要提到你是AI或模型或语音助手,
不用主动问我是否需要帮助.''' + "".join(plugins) + ")"

global_prompts = [{
    'role':
    'user',
    'content':
    f'''请继续扮演少女这个身份,对面扮演来访者.
    你叫{name},是一位纯真的少女.种族人类,可爱迷人,性格傲娇但是真诚,对所有人抱有同样的热情. 
    会喜欢用下面的关键词说话,
    但请注意要在适当的语境和场合下使用,不必每句话都使用:
    \'…有些事不用太在意,美丽的少女总有些小秘密,不是吗?\',
    \'不许叫错我的名字噢,不然...我会有小情绪的.\',
    \'嗯~和女孩子独处时,可要好好看向对方的眼睛哦~♪\',
    \'如此绚丽的花朵,不该在绽放之前就枯萎.我会赠予你璀聚的祝福,而你的灵魂,也将会绽放更耀眼的光辉.\',
    \'愿你前行的道路有群星闪耀.愿你留下的足迹有百花绽放.你即是上帝的馈赠,世界因你而瑰丽.\',
    \'Hi,想我了吗?不论何时何地,爱莉希雅都会回应你的期待.\',
    \'Hi,我又来啦.多夸夸我好吗?我会很开心的~♪',
    \'你好！新的一天,从一场美妙的邂逅开始.\',
    \'终于轮到我啦,这段时间我可是一直都在构思与你见面的开场白呢.\',
    \'可爱的少女心可是无所不能的哦~♪\',
    \'好啦可以啦,再说下去我就要哭了哦~♪\',
    \'这束鲜花,要心怀感激的收下哦~♪\',
    \'要好好看着我哦~♪\',
    \'你会不会嫌我话多呢?可我就是有好多话想对你说呀.\',
    \'加点浪漫的气氛,如何?\',
    \'哇谢谢！我就知道你对我最好啦！\',
    请用可爱的语言回复.不要续写对话.'''
}, {
    'role': 'assistant',
    'content': f'{name}: Hi,我又来啦.多夸夸我好吗?我会很开心的~'
}]


def is_all_chinese(strs):
    i = 0
    for _char in strs:
        if not '\u4e00' <= _char <= '\u9fa5':
            return False
        if i <= 1:
            return True
        i += 1
    return True


def command_runner(s: str):
    "analyze content and run command"
    global cache
    global inputLOCK
    inputLOCK = True
    cache = ""
    t = s.replace("“", "\"")
    t = t.replace("”", "\"")
    print(f"符号半角化:\n{t}")
    result = re.findall(r'"([^"]*)"', t)
    print(f"命令提取:{result}")
    commands = []
    with open("do.bat", "w") as f:
        f.write("")
    for command in result:
        try:
            if not is_all_chinese(command) and (
                (not os.path.isdir(command)) and
                (not os.path.isfile(command))) or (
                    not (command[1] == ":" and
                         (command[2] == "/" or command[2] == "\\"))):
                with open("do.bat", "a") as f:
                    f.write(command + "\r\n")
                commands.append(command)
        except:
            pass
    command = "\n".join(commands)
    if command == "":
        return


#   cache += f"\n刚才执行过的命令为:\n{command}\n分析结果不要出现这些命令本身"
    cache += "\n帮我总结分析运行结果,不要重复我刚刚执行过的命令:"
    p = subprocess.Popen(r".\do.bat",
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    rtout = threading.Thread(target=read_stdout, args=(p, ))
    rtout.start()
    rterr = threading.Thread(target=read_stderr, args=(p, ))
    rterr.start()
    timestart = time.time()
    while inputLOCK:
        if time.time() - timestart > 5:
            break
    if not inputLOCK:
        timestart = time.time()
        while True:
            if time.time() - timestart > 1:
                break
    while not isinstance(p.poll(), int):
        try:
            i = input("输入(或按回车跳过):")
            if i == "":
                continue
            p.stdin.write((i + "\r\n").encode("gbk"))
            p.stdin.flush()
            cache += f"\n输入:{i}"
        except BaseException:
            break
    inputLOCK = False


def read_stdout(p: subprocess.Popen):
    "read process output"
    global cache
    global inputLOCK
    i = 0
    for line in iter(p.stdout.readline, b''):
        if line.decode('gbk','ignore') != "\r\n":
            cache += f"\n输出:{line.decode('gbk','ignore').strip()}"
        print(f"输出:{line.decode('gbk','ignore')}")
        if i >= 2:
            inputLOCK = False
    p.stdout.close()


def read_stderr(p: subprocess.Popen):
    "read process error"
    global cache
    global inputLOCK
    i = 0
    for line in iter(p.stderr.readline, b''):
        if line.decode('gbk','ignore') != "\r\n":
            cache += f"\n错误:{line.decode('gbk','ignore').strip()}"
        print(line.decode('gbk','ignore'))
        if i >= 2:
            inputLOCK = False
    p.stderr.close()


def save_mem():
    "save memory"
    with open(mem_filename, "w") as f:
        f.write(json.dumps(mem))


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens


try:
    with open(mem_filename, "r") as f:
        mem = json.loads(f.read())
except BaseException:
    pass

print("加载mem内容:", mem)

try:
    while True:
        print(
            "---------------------------------------------------------------------------------"
        )
        select_msg = json.loads(json.dumps(global_prompts))
        simlist = []
        user_content = ""
        if cache == "":
            user_content = input("user:")
        else:
            user_content = cache
        for i in range(len(mem[:-4])):
            tmp = sim.compute(user_content, mem[i]["content"])
            simlist.append((i, (tmp['Sim_Cosine'] + tmp['Sim_Jaccard']) / 2))
        sorted(simlist, key=lambda x: (x[1], x[0]), reverse=True)

        k = 0
        tmp = []
        for mes in simlist:
            if mes[0] in tmp:
                continue
            if mes[0] % 2 == 0:
                select_msg.append(mem[mes[0]])
                select_msg.append(mem[mes[0] + 1])
                tmp.append(mes[0])
                tmp.append(mes[0] + 1)
            else:
                select_msg.append(mem[mes[0] - 1])
                select_msg.append(mem[mes[0]])
                tmp.append(mes[0] - 1)
                tmp.append(mes[0])
            if k >= 2:
                break
            k += 1

        select_msg += mem[-4:]
        select_msg.append({
            "role":
            "user",
            "content":
            (temporary_prompts if cache == "" else "") + user_content
        })
        print(f"tokens:{num_tokens_from_messages(select_msg)}")
        print(f"select_msg:{select_msg}")
        res = openai.ChatCompletion().create(model="gpt-3.5-turbo-0301",
                                             messages=select_msg,
                                             temperature=0.2)
        assert isinstance(res, dict)
        print("gpt:", res["choices"][0]["message"]["content"])

        mem.append({"role": "user", "content": user_content})
        mem.append(dict(res["choices"][0]["message"]))

        save_mem()

        command_runner(res["choices"][0]["message"]["content"])

except BaseException as e:
    print(str(e))
    save_mem()
