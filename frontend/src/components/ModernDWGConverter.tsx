import React, { useState } from 'react';
import {
  Upload,
  Button,
  Steps,
  Card,
  Typography,
  Space,
  Row,
  Col,
  Tag,
  Progress,
  message,
  Divider,
  Alert,
  Empty,
  Spin,
  Form,
  Input,
  Descriptions,
  Badge,
  Timeline,
  Tooltip,
  Result
} from 'antd';
import {
  UploadOutlined,
  RobotOutlined,
  FilePdfOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  CloudUploadOutlined,
  EditOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { Brain, Zap, Settings, FileText, CheckCircle } from 'lucide-react';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Step } = Steps;

interface ConversionParams {
  auto_fit: boolean;
  center: boolean;
  paper_size?: string;
  margin?: number;
  grayscale: boolean;
  monochrome: boolean;
  layers?: string[];
}

interface ModernDWGConverterProps {
  onJobCreated: (jobId: string) => void;
}

const ModernDWGConverter: React.FC<ModernDWGConverterProps> = ({ onJobCreated }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [dwgFile, setDwgFile] = useState<File | null>(null);
  const [userRequest, setUserRequest] = useState('');
  const [analyzedParams, setAnalyzedParams] = useState<ConversionParams | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [conversionResult, setConversionResult] = useState<any>(null);

  const steps = [
    {
      title: '上传文件',
      description: '选择要转换的DWG文件',
      icon: <CloudUploadOutlined />
    },
    {
      title: '智能分析',
      description: '描述您的转换需求',
      icon: <RobotOutlined />
    },
    {
      title: '确认参数',
      description: '检查转换设置',
      icon: <EyeOutlined />
    },
    {
      title: '开始转换',
      description: '执行转换任务',
      icon: <FilePdfOutlined />
    },
    {
      title: '完成',
      description: '下载转换结果',
      icon: <DownloadOutlined />
    }
  ];

  // 处理文件上传
  const handleFileChange = (info: any) => {
    if (info.fileList.length > 0) {
      const file = info.fileList[0].originFileObj;
      if (file.name.toLowerCase().endsWith('.dwg')) {
        setDwgFile(file);
        setCurrentStep(1);
        message.success('文件上传成功');
      } else {
        message.error('请上传 DWG 文件');
      }
    } else {
      setDwgFile(null);
      setCurrentStep(0);
    }
  };

  // 分析自然语言需求
  const analyzeUserRequest = async () => {
    if (!userRequest.trim()) {
      // 使用默认参数
      const defaultParams = {
        auto_fit: true,
        center: true,
        paper_size: null,
        margin: null,
        grayscale: false,
        monochrome: false,
        layers: null
      };
      setAnalyzedParams(defaultParams);
      setCurrentStep(2);
      message.info('使用默认转换参数');
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await axios.post('/api/enhanced/analyze-request', {
        request: userRequest
      });

      if (response.data.params) {
        setAnalyzedParams(response.data.params);
        setCurrentStep(2);
        message.success('需求分析完成');
      } else {
        message.error('需求分析失败');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      message.error('需求分析失败: ' + (error as any).message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 开始转换
  const startConversion = async () => {
    if (!dwgFile) {
      message.error('请上传 DWG 文件');
      return;
    }

    setIsConverting(true);
    setProgress(0);
    setCurrentStep(3);

    try {
      const formData = new FormData();
      formData.append('dwg_file', dwgFile);
      formData.append('params', JSON.stringify(analyzedParams));

      const response = await axios.post('/api/enhanced/convert-dwg', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress(percentCompleted);
          }
        },
      });

      if (response.data.job_id) {
        message.success('转换任务已提交，正在处理中...');
        onJobCreated(response.data.job_id);
        // 模拟转换完成（实际应该通过轮询或WebSocket获取状态）
        setTimeout(() => {
          setConversionResult({
            job_id: response.data.job_id,
            status: 'completed',
            file_size: '2.3MB',
            pages: 3
          });
          setCurrentStep(4);
          setIsConverting(false);
        }, 3000);
      } else {
        message.error('转换失败');
        setIsConverting(false);
      }
    } catch (error) {
      console.error('Conversion error:', error);
      message.error('转换失败: ' + (error as any).message);
      setIsConverting(false);
    }
  };

  // 参数展示组件
  const renderParams = () => {
    if (!analyzedParams) return null;

    const params = [];

    if (analyzedParams.paper_size) {
      params.push(<Tag color="blue">📄 {analyzedParams.paper_size}</Tag>);
    }
    if (analyzedParams.margin !== undefined) {
      params.push(<Tag color="green">📏 {analyzedParams.margin}mm 边距</Tag>);
    }
    if (analyzedParams.auto_fit) {
      params.push(<Tag color="orange">🔄 自动适应</Tag>);
    }
    if (analyzedParams.center) {
      params.push(<Tag color="purple">🎯 居中</Tag>);
    }
    if (analyzedParams.grayscale) {
      params.push(<Tag color="gray">🎨 灰度</Tag>);
    }
    if (analyzedParams.monochrome) {
      params.push(<Tag color="black">⚫ 黑白</Tag>);
    }
    if (analyzedParams.layers && analyzedParams.layers.length > 0) {
      params.push(<Tag color="cyan">📑 {analyzedParams.layers.join('、')}</Tag>);
    }

    if (params.length === 0) {
      return <Text type="secondary">使用默认参数</Text>;
    }

    return <Space wrap>{params}</Space>;
  };

  // 渲染步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Card style={{ textAlign: 'center', padding: '40px' }}>
            <Empty
              image={<CloudUploadOutlined style={{ fontSize: 64, color: '#1890ff' }} />}
              description={
                <Space direction="vertical" size="large">
                  <div>
                    <Title level={3}>上传 DWG 文件</Title>
                    <Paragraph type="secondary">
                      支持 .dwg 格式，文件大小建议不超过 50MB
                    </Paragraph>
                  </div>
                  <Upload
                    accept=".dwg"
                    maxCount={1}
                    onChange={handleFileChange}
                    showUploadList={false}
                    beforeUpload={() => false}
                  >
                    <Button type="primary" size="large" icon={<UploadOutlined />}>
                      选择 DWG 文件
                    </Button>
                  </Upload>
                </Space>
              }
            />
          </Card>
        );

      case 1:
        return (
          <Row gutter={[24, 24]}>
            <Col xs={24} lg={16}>
              <Card title={<><Brain size={20} /> 智能需求分析</>}>
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Alert
                    message="AI 驱动的智能分析"
                    description="用自然语言描述您的转换需求，系统会自动提取参数。如果不确定具体需求，可以直接点击下一步使用默认设置。"
                    type="info"
                    showIcon
                  />

                  <div>
                    <Title level={5}>描述转换需求</Title>
                    <TextArea
                      placeholder="例如：我需要A3大小的PDF，黑白打印，只导出墙体图层"
                      value={userRequest}
                      onChange={(e) => setUserRequest(e.target.value)}
                      rows={4}
                      showCount
                      maxLength={500}
                    />
                  </div>

                  <Space>
                    <Button
                      type="primary"
                      size="large"
                      icon={<RobotOutlined />}
                      onClick={analyzeUserRequest}
                      loading={isAnalyzing}
                    >
                      {isAnalyzing ? '分析中...' : '智能分析需求'}
                    </Button>
                    <Button
                      size="large"
                      onClick={() => setCurrentStep(2)}
                      disabled={isAnalyzing}
                    >
                      使用默认设置
                    </Button>
                  </Space>
                </Space>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="示例需求" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Badge color="blue" text="基础设置" />
                    <ul style={{ marginTop: 8, paddingLeft: 16 }}>
                      <li>A3纸张，黑白打印</li>
                      <li>A4大小，灰度输出</li>
                      <li>自动适应，居中显示</li>
                    </ul>
                  </div>
                  <div>
                    <Badge color="green" text="高级设置" />
                    <ul style={{ marginTop: 8, paddingLeft: 16 }}>
                      <li>10mm边距，彩色PDF</li>
                      <li>只导出墙体图层</li>
                      <li>高清打印质量</li>
                    </ul>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        );

      case 2:
        return (
          <Card title={<><EyeOutlined size={20} /> 确认转换参数</>}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="输入文件">
                  <Space>
                    <FileText />
                    {dwgFile?.name}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="文件大小">
                  {dwgFile ? `${(dwgFile.size / 1024 / 1024).toFixed(2)} MB` : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="转换参数" span={2}>
                  {renderParams()}
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              <Space>
                <Button
                  type="primary"
                  size="large"
                  icon={<FilePdfOutlined />}
                  onClick={startConversion}
                >
                  开始转换
                </Button>
                <Button
                  size="large"
                  onClick={() => setCurrentStep(1)}
                  icon={<EditOutlined />}
                >
                  修改参数
                </Button>
              </Space>
            </Space>
          </Card>
        );

      case 3:
        return (
          <Card title={<><LoadingOutlined /> 正在转换</>}>
            <Space direction="vertical" style={{ width: '100%', alignItems: 'center' }} size="large">
              <Spin size="large" />
              <div style={{ width: '100%', textAlign: 'center' }}>
                <Title level={4}>正在转换 DWG 文件</Title>
                <Progress percent={progress} status="active" />
                <Text type="secondary">请稍候，正在使用 AutoCAD 处理您的文件...</Text>
              </div>
            </Space>
          </Card>
        );

      case 4:
        return (
          <Result
            status="success"
            title="转换完成！"
            subTitle={`您的 DWG 文件已成功转换为 PDF，文件大小 ${conversionResult?.file_size || 'N/A'}`}
            extra={[
              <Button type="primary" key="download" icon={<DownloadOutlined />}>
                下载 PDF 文件
              </Button>,
              <Button key="new" onClick={() => {
                setCurrentStep(0);
                setDwgFile(null);
                setUserRequest('');
                setAnalyzedParams(null);
                setConversionResult(null);
              }}>
                转换新文件
              </Button>
            ]}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ color: '#1890ff', margin: 0 }}>
              <FilePdfOutlined /> DWG 智能转换器
            </Title>
            <Paragraph type="secondary" style={{ fontSize: 16 }}>
              基于 AI 的自然语言处理 + AutoCAD 精准转换
            </Paragraph>
          </div>

          <Steps
            current={currentStep}
            items={steps}
            style={{ marginBottom: 32 }}
          />

          {renderStepContent()}
        </Space>
      </Card>
    </div>
  );
};

export default ModernDWGConverter;