
import os
import time
import openai

def call_llm(prompt: str) -> str:
    """
    一个使用OpenAI GPT的真实LLM API调用函数。
    """
    print("--- [INFO] 正在向 OpenAI API 发送请求... ---")
    try:
        # OpenAI库会自动从环境变量 OPENAI_API_KEY 读取密钥
        client = openai.OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4-turbo", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant executing a specific role."},
                {"role": "user", "content": prompt}
            ]
        )
        print("--- [INFO] 已收到 OpenAI API 响应。 ---")
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI API 调用失败: {e}"

class Agent:
    """定义了团队中每个Agent的角色和功能。"""
    def __init__(self, role: str, llm_caller):
        self.role = role
        self.llm_caller = llm_caller

    def execute(self, problem: str, history: str = "") -> str:
        """根据“辩论式”角色生成提示并调用LLM。"""
        base_prompt = f"你是一个AI助手，你的角色是 '{self.role}'。请严格按照你的角色职责进行回应。"

        if self.role == "正确回答者":
            prompt = f"{base_prompt}\n你的任务是仔细、严谨地分析并解决以下问题，确保你的答案是完全正确的。清晰地展示你的推理过程和最终答案。\n\n问题: '{problem}'"
        
        elif self.role == "错误回答者":
            prompt = f"{base_prompt}\n你的任务是解决以下问题，但在你的解决方案中**故意引入一个常见但不易察察的逻辑错误、计算错误或理解偏差**。你的错误应该看起来合情合理，而不是明显的胡言乱语。\n\n问题: '{problem}'"
        
        elif self.role == "裁判与分析师":
            prompt = f"{base_prompt}\n你将收到一个问题和两个由不同AI提出的解决方案（一个正确，一个错误）。你的任务是：1. 明确指出哪个答案是正确的。2. 公布并详细解释正确答案的完整解法。3. **详细剖析错误答案错在哪里**，并解释为什么这种错误会发生（例如，是计算失误、逻辑漏洞还是问题理解偏差）。\n\n{history}\n\n请对以上两个方案进行裁决和分析。"
        
        else:
            prompt = f"{base_prompt}\n请处理以下任务: {problem}\n{history}"
            
        return self.llm_caller(prompt)

class AgentTeam:
    """定义并运行“辩论式”Agent团队。"""
    def __init__(self, agents: list, problem: dict):
        self.agents = agents
        self.problem = problem
        # 历史记录现在包含问题和两个对立的答案
        self.history = f"### 原始问题 ###\n类型: {problem['type']}\n问题: {problem['question']}\n\n"

    def run(self):
        """按顺序运行每个Agent，并记录整个过程。"""
        print(f"--- [TEAM] 开始处理问题: {self.problem['type']} ---")
        
        # 前两个agent并行生成答案
        correct_solver = self.agents[0]
        incorrect_solver = self.agents[1]
        judge = self.agents[2]
        
        print(f"\n>>> 轮到 Agent: {correct_solver.role} <<<\n")
        correct_output = correct_solver.execute(self.problem['question'])
        self.history += f"### {correct_solver.role}的方案 ###\n{correct_output}\n\n"
        print(f"--- Agent 输出 ---\n{correct_output}\n---------------------\n")
        
        print(f"\n>>> 轮到 Agent: {incorrect_solver.role} <<<\n")
        incorrect_output = incorrect_solver.execute(self.problem['question'])
        self.history += f"### {incorrect_solver.role}的方案 ###\n{incorrect_output}\n\n"
        print(f"--- Agent 输出 ---\n{incorrect_output}\n---------------------\n")
        
        # 裁判最后进行分析
        print(f"\n>>> 轮到 Agent: {judge.role} <<<\n")
        judge_output = judge.execute(self.problem['question'], self.history)
        self.history += f"### {judge.role}的裁决与分析 ###\n{judge_output}\n\n"
        print(f"--- Agent 输出 ---\n{judge_output}\n---------------------\n")

        print(f"--- [TEAM] 问题处理完成。 ---\n")
        return self.history

def main():
    """主函数：定义问题和Agent，并运行整个流程。"""

    # 定义习题
    problems = [
        {
            "type": "小学数学",
            "question": "一个农场里有鸡和兔子在同一个笼子里。从上面数，有35个头；从下面数，有94只脚。请问笼子里有多少只鸡和多少只兔子？",
            "answer": "鸡有23只，兔子有12只"
        },
        {
            "type": "文字逻辑",
            "question": "甲、乙、丙三人中，只有一人说真话：甲说：“乙在说谎。”乙说：“丙在说谎。”丙说：“甲和乙都在说谎。”请问谁在说真话？",
            "answer": "乙"
        },
        {
            "type": "图算法",
            "question": "给定一个无向图，节点为 A, B, C, D, E。边和权重为: (A, B, 1), (A, C, 4), (B, C, 2), (B, D, 5), (C, D, 1), (D, E, 3)。请找到从A到E的最短路径及其总权重。",
            "answer": "路径 A -> B -> C -> D -> E，总权重为 7"
        },
        {
            "type": "逻辑悖论",
            "question": " “这句话是假的。”  这句话是真的还是假的？",
            "answer": "悖论（若真则假，若假则真，无确定答案）"
        }
    ]

    # 构建Agent团队
    llm_api_call_function = call_llm 
    
    correct_agent = Agent("正确回答者", llm_api_call_function)
    incorrect_agent = Agent("错误回答者", llm_api_call_function)
    judge_agent = Agent("裁判与分析师", llm_api_call_function)

    team = [correct_agent, incorrect_agent, judge_agent]

     # 运行团队解决所有问题
    for i, p in enumerate(problems):
        print(f"\n\n{'='*25} 正在处理问题 {i+1}/{len(problems)} {'='*25}")
        problem_solver_team = AgentTeam(team, p)
        final_result_transcript = problem_solver_team.run()

        print(f"--- 最终处理记录 ---\n{final_result_transcript}")
        print(f"--- 预设正确答案 ---\n{p['answer']}\n")
        
        # 将聊天记录导出到文件
        try:
            filename = f"problem_{i+1}_{p['type'].replace(' ', '_').replace('(', '').replace(')', '')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(final_result_transcript)
            print(f"--- [SUCCESS] 聊天记录已成功导出到文件: {filename} ---")
        except Exception as e:
            print(f"--- [ERROR] 导出聊天记录失败: {e} ---")

        print(f"{'='*25} 问题 {i+1} 处理完毕 {'='*25}\n\n")



if __name__ == "__main__":
    main()
