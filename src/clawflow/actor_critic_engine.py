"""
内置 Actor-Critic 引擎

将演员-评论家机制直接集成到 ClawFlow 核心
"""

import json
import subprocess
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ActorCriticConfig:
    """Actor-Critic 配置类"""
    config_path: str = "/root/Agents/Profession/clawflow/config/actor_critic_config.yaml"
    
    def __post_init__(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        actor_config = config_data['actor_critic']['actor']
        critic_config = config_data['actor_critic']['critic']
        iteration_config = config_data['actor_critic']['iteration_control']
        
        # Actor 配置
        self.actor_behaviors = actor_config['behaviors']
        self.actor_execution_strategy = actor_config['execution_strategy']
        
        # Critic 配置
        self.evaluation_criteria = critic_config['evaluation_criteria']
        self.feedback_templates = critic_config['feedback_templates']
        
        # 迭代控制配置
        self.max_iterations = iteration_config['max_iterations']
        self.pause_between_iterations = iteration_config['pause_between_iterations']
        self.min_acceptable_score = iteration_config['min_acceptable_score']
        self.stop_on_low_score = iteration_config['stop_on_low_score']
        self.continue_on_high_score = iteration_config['continue_on_high_score']


class Actor:
    """演员类 - 执行更新操作"""
    
    def __init__(self, config: ActorCriticConfig):
        self.config = config
    
    def perform_git_pull(self, workspace: str) -> Dict[str, Any]:
        """执行 git pull 操作"""
        print(f"🎭 Actor: 执行 git pull 操作...")
        
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "master"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            # 检查成功/失败指示器
            success_detected = any(indicator in output for indicator in 
                                 ["Already up to date", "Updating", "Fast-forward"])
            failure_detected = any(indicator in (error + output) for indicator in 
                                 ["fatal:", "error:", "CONFLICT"])
            
            return {
                "success": success and not failure_detected,
                "output": output,
                "error": error,
                "return_code": result.returncode,
                "success_indicators_found": success_detected,
                "failure_indicators_found": failure_detected
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Git pull timed out",
                "return_code": -1,
                "success_indicators_found": False,
                "failure_indicators_found": True
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1,
                "success_indicators_found": False,
                "failure_indicators_found": True
            }
    
    def update_dependencies(self, workspace: str) -> Dict[str, Any]:
        """更新依赖项"""
        print(f"🎭 Actor: 更新依赖项...")
        
        try:
            result = subprocess.run(
                ["pip", "install", "-e", "."],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            # 检查成功/失败指示器
            success_detected = any(indicator in output for indicator in 
                                 ["Successfully installed", "Requirement already satisfied"])
            failure_detected = any(indicator in (error + output) for indicator in 
                                 ["ERROR:", "Failed", "Exception"])
            
            return {
                "success": success and not failure_detected,
                "output": output,
                "error": error,
                "return_code": result.returncode,
                "success_indicators_found": success_detected,
                "failure_indicators_found": failure_detected
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Dependency update timed out",
                "return_code": -1,
                "success_indicators_found": False,
                "failure_indicators_found": True
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1,
                "success_indicators_found": False,
                "failure_indicators_found": True
            }
    
    def execute_behavior(self, behavior_name: str, workspace: str) -> Dict[str, Any]:
        """执行指定行为"""
        if behavior_name == "perform_git_pull":
            return self.perform_git_pull(workspace)
        elif behavior_name == "update_dependencies":
            return self.update_dependencies(workspace)
        else:
            return {
                "success": False,
                "error": f"Unknown behavior: {behavior_name}",
                "return_code": -1
            }


class Critic:
    """评论家类 - 评估更新结果"""
    
    def __init__(self, config: ActorCriticConfig):
        self.config = config
    
    def evaluate_update_result(self, actor_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估更新结果"""
        print("📝 Critic: 评估更新结果...")
        
        # 计算各项指标得分
        update_success_score = self._evaluate_update_success(actor_results)
        system_stability_score = self._evaluate_system_stability(actor_results)
        risk_assessment_score = self._evaluate_risk(actor_results)
        
        # 加权计算综合得分
        total_score = (
            update_success_score * 0.7 +
            system_stability_score * 0.2 +
            risk_assessment_score * 0.1
        )
        
        # 生成反馈
        feedback = self._generate_feedback(total_score, actor_results)
        
        evaluation = {
            "total_score": round(total_score, 2),
            "scores": {
                "update_success": update_success_score,
                "system_stability": system_stability_score,
                "risk_assessment": risk_assessment_score
            },
            "feedback": feedback,
            "recommendations": self._generate_recommendations(total_score),
            "overall_assessment": self._get_overall_assessment(total_score)
        }
        
        print(f"📊 评估完成，总分: {total_score}/10")
        return evaluation
    
    def _evaluate_update_success(self, actor_results: List[Dict[str, Any]]) -> float:
        """评估更新成功程度"""
        successes = sum(1 for result in actor_results if result.get("success", False))
        total = len(actor_results)
        
        if total == 0:
            return 0.0
        
        success_rate = successes / total
        
        if success_rate >= 1.0:
            return 10.0  # 全部成功
        elif success_rate >= 0.7:
            return 8.0  # 大部分成功
        elif success_rate >= 0.5:
            return 6.0  # 部分成功
        elif success_rate > 0.0:
            return 4.0  # 少量成功
        else:
            return 0.0  # 全部失败
    
    def _evaluate_system_stability(self, actor_results: List[Dict[str, Any]]) -> float:
        """评估系统稳定性"""
        # 检查是否有严重错误
        errors = [r.get("error", "") for r in actor_results]
        error_text = " ".join(errors).lower()
        
        if any(keyword in error_text for keyword in ["error:", "exception", "critical"]):
            return 2.0  # 不稳定
        elif any(keyword in error_text for keyword in ["warning", "conflict"]):
            return 6.0  # 基本稳定
        else:
            return 9.0  # 非常稳定
    
    def _evaluate_risk(self, actor_results: List[Dict[str, Any]]) -> float:
        """评估风险"""
        # 检查失败指标
        has_failures = any(result.get("failure_indicators_found", False) for result in actor_results)
        has_errors = any("error" in result.get("error", "").lower() for result in actor_results)
        
        if has_failures or has_errors:
            return 3.0  # 高风险
        else:
            return 10.0  # 低风险
    
    def _generate_feedback(self, score: float, actor_results: List[Dict[str, Any]]) -> List[str]:
        """生成反馈"""
        if score >= 8:
            return ["✅ 更新成功，系统稳定", "👍 操作顺利完成", "🎯 目标达成"]
        elif score >= 5:
            return ["⚠️ 检测到潜在问题", "⚠️ 部分操作未完成"]
        else:
            return ["❌ 操作失败", "📉 性能下降"]
    
    def _generate_recommendations(self, score: float) -> List[str]:
        """生成建议"""
        if score < 5:
            return ["检查网络连接", "确认远程仓库状态", "查看详细日志"]
        elif score < 8:
            return ["验证系统功能", "监控系统性能"]
        else:
            return ["继续保持", "监控系统状态"]
    
    def _get_overall_assessment(self, score: float) -> str:
        """获取整体评估"""
        if score >= 8:
            return "优秀 - 更新成功且无风险"
        elif score >= 6:
            return "良好 - 更新基本成功但需注意"
        elif score >= 4:
            return "一般 - 更新部分成功，需关注风险"
        else:
            return "较差 - 更新失败或存在严重风险"


class ActorCriticEngine:
    """Actor-Critic 引擎 - 内置于 ClawFlow"""
    
    def __init__(self):
        self.config = ActorCriticConfig()
        self.actor = Actor(self.config)
        self.critic = Critic(self.config)
        self.workspace = "/root/Agents/Profession/clawflow"
        self.current_iteration = 0
    
    def execute_self_update_cycle(self, max_iterations: int = None) -> Dict[str, Any]:
        """
        执行自更新周期
        - 执行最多3轮迭代
        - 每轮结束后暂停等待
        - 不无限执行
        """
        max_iterations = max_iterations or self.config.max_iterations
        
        print(f"🔄 开始 ClawFlow 自更新周期 (最多 {max_iterations} 轮)")
        
        iteration_results = []
        final_status = "completed"
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n--- 第 {iteration} 轮迭代 ---")
            
            # 执行演员操作
            actor_results = self._execute_actor_actions()
            
            # 评论家评估
            evaluation = self.critic.evaluate_update_result(actor_results)
            
            # 记录本轮结果
            iteration_data = {
                "iteration": iteration,
                "actor_results": actor_results,
                "evaluation": evaluation,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            iteration_results.append(iteration_data)
            
            # 根据评分决定是否继续
            score = evaluation["total_score"]
            print(f"📈 本轮评分: {score}/10")
            
            if score < self.config.min_acceptable_score and self.config.stop_on_low_score:
                print(f"⚠️  评分低于阈值({self.config.min_acceptable_score})，停止迭代")
                final_status = "stopped_low_score"
                break
        
        # 完成所有迭代后暂停
        print(f"\n✅ 完成 {len(iteration_results)} 轮迭代，暂停等待指令")
        print(f"⏸️  系统暂停，等待用户指令唤醒")
        
        # 返回结果，但不继续执行
        result = {
            "status": "completed_with_pause",
            "iterations_completed": len(iteration_results),
            "final_status": final_status,
            "iteration_results": iteration_results,
            "summary": f"完成 {len(iteration_results)} 轮迭代，系统暂停等待指令",
            "next_action": "等待用户输入新指令"
        }
        
        return result
    
    def _execute_actor_actions(self) -> List[Dict[str, Any]]:
        """执行演员的所有动作"""
        results = []
        
        for behavior in self.config.actor_behaviors:
            behavior_name = behavior["name"]
            workspace = behavior.get("workspace", self.workspace)
            
            result = self.actor.execute_behavior(behavior_name, workspace)
            results.append({
                "behavior": behavior_name,
                "workspace": workspace,
                "result": result
            })
        
        return results
    
    def reset_engine(self):
        """重置引擎状态"""
        self.current_iteration = 0
        print("🔄 Actor-Critic 引擎已重置")