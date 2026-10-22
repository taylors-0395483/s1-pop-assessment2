# 校园电动汽车充电分析

Taylor's 编程原理 Assessment 2 小组项目：处理充电数据、比较两个分类模型，并通过支持中英文的 Streamlit 网页展示结果。

[English](README.md)

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `0_ev_campus_dataset.csv` | 当前工作数据，包含 1,200 条记录，已经清洗并增加功率、高峰时段字段。 |
| `task1_data_pipeline.py` | 用中位数填补数值缺失、按记录编号去重、计算特征并输出分组统计。 |
| `task2_train_model.py` | 按 80%/20% 划分训练集和测试集，训练、评估决策树与随机森林。 |
| `task2_ev_model.pkl` | 选出的随机森林模型，以及预测需要的输入和编码信息。 |
| `task2_model_comparison.csv` | 两个模型的准确率，以及宏平均精确率、召回率和 F1。 |
| `task2_confusion_matrices.png` | 两个模型在测试集上的混淆矩阵。 |
| `task3_app.py` | 中英文网页，包含数据概览、图表分析和状态预测。 |
| `requirements.txt` | 本地安装及云端部署使用的 Python 依赖版本。 |
| `packages.txt` | 云端 Linux 环境绘制中文图表需要的字体。 |

## 本地运行

使用 Python 3.12。在终端进入本项目目录，安装保存模型和本地网页使用的依赖版本：

```bash
python -m pip install -r requirements.txt
```

仓库已包含处理后的数据和训练好的模型，可以直接启动网页：

```bash
python -m streamlit run task3_app.py
```

打开终端输出的本地网址。停止运行时按 `Ctrl+C`。

使用 PyCharm 时，选择安装了上述依赖的 Python 环境，将 `task3_app.py` 作为普通 Python 脚本运行即可；它会自动启动 Streamlit。请选择 **Run**，不要使用单元测试运行配置。

## 重新执行 Task 1 和 Task 2

使用仓库现有的数据和模型时，可以跳过这两步。需要重新生成结果时，按顺序执行：

```bash
python task1_data_pipeline.py
python task2_train_model.py
```

Task 1 会**覆盖同一份 `0_ev_campus_dataset.csv`**。当前 CSV 已经处理过，再运行时不会重新出现最初的缺失值。Task 2 会覆盖对应的三个产物文件。替换数据或模型后，请重启网页以刷新缓存。

## 网页使用方法

- **数据概览**：筛选记录，查看充电量、平均时长和估算收入，下载筛选后的 CSV。
- **图表分析**：查看充电量与电池温度的关系、充电桩类型数量，以及高峰与非高峰平均充电量。
- **状态预测**：填写充电参数，点击“预测状态”，得到正常、电网负荷突增或过热的预测结果。
- 右上角可以切换中英文；下载的 CSV 保留原始字段名和类别代码。

终端或 PyCharm 控制台会输出以 `[TASK3]` 开头的操作日志，包括筛选变化、图表生成、下载请求和已提交的预测；不会另外创建日志文件。

## 部署到 Streamlit Community Cloud

将项目文件、`requirements.txt` 和 `packages.txt` 推送到 GitHub 后：

1. 登录 [Streamlit Community Cloud](https://share.streamlit.io/)，选择 **Create app** → **Yup, I have an app**。
2. 仓库填写 `taylors-0395483/s1-pop-assessment2`，分支填写 `main`，入口文件填写 `task3_app.py`。
3. 在 **Advanced settings** 中选择 **Python 3.12**。本项目不需要填写 API 密钥或 Secrets。
4. 点击 **Deploy**，等待依赖安装完成。平台会读取两个依赖文件并启动网页；部署时不需要运行清洗或训练脚本。
5. 打开生成的网址，检查中英文、筛选、CSV 下载、三张图表和一次提交后的预测。

`packages.txt` 会在云端 Linux 安装文泉驿正黑字体，现有代码已经支持自动选用它。图表使用 Matplotlib 的 `Agg` 后端，不需要桌面图形界面。

参考官方[部署说明](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)和[依赖说明](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)。

## 当前规则与结果

- 平均充电功率：`Power_kW = Energy_kWh / (Duration_Mins / 60)`。
- 高峰时段为 **12:00–17:00**，按充电过程是否与该时段重叠判断。当前采用已有的 AC/DC 充电桩分组，没有另外生成效率类别。
- 收入根据 Assessment 1 的收费规则及现有字段估算。碳减排量需要自行输入系数；可选的温度提醒也需要自行设置阈值。

| 模型 | 测试准确率 | 宏平均 F1 |
| --- | --- | --- |
| 随机森林 | 85.00% | 0.7674 |
| 决策树 | 83.75% | 0.7444 |

模型文件只保存选出的随机森林。预测可能有误，尤其是电网负荷突增类别。目前网页在本地运行，云端部署和演示视频尚待完成。
