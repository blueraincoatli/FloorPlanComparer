import React, { useState } from 'react';
import {
  Upload,
  Button,
  message,
  Spin,
  Progress,
  Card,
  Typography,
  Space,
  Input,
  Row,
  Col,
  Tag,
  Divider
} from 'antd';
import {
  UploadOutlined,
  FilePdfOutlined,
  RobotOutlined,
  SettingOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface ConversionParams {
  auto_fit: boolean;
  center: boolean;
  paper_size?: string;
  margin?: number;
  grayscale: boolean;
  monochrome: boolean;
}

interface DWGConverterProps {
  onJobCreated: (jobId: string) => void;
}

const DWGConverter: React.FC<DWGConverterProps> = ({ onJobCreated }) => {
  const [dwgFile, setDwgFile] = useState<File | null>(null);
  const [userRequest, setUserRequest] = useState('');
  const [analyzedParams, setAnalyzedParams] = useState<ConversionParams | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [progress, setProgress] = useState(0);

  // 处理文件上传
  const handleFileChange = (info: any) => {
    if (info.fileList.length > 0) {
      const file = info.fileList[0].originFileObj;
      if (file.name.toLowerCase().endsWith('.dwg')) {
        setDwgFile(file);
      } else {
        message.error('请上传 DWG 文件');
      }
    } else {
      setDwgFile(null);
    }
  };

  // 分析自然语言需求
  const analyzeUserRequest = async () => {
    if (!userRequest.trim()) {
      // 如果用户没有输入需求，使用默认参数
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

    if (!analyzedParams) {
      message.warning('请先分析转换需求');
      return;
    }

    setIsConverting(true);
    setProgress(0);

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
      } else {
        message.error('转换失败');
      }
    } catch (error) {
      console.error('Conversion error:', error);
      message.error('转换失败: ' + (error as any).message);
    } finally {
      setIsConverting(false);
      setProgress(0);
    }
  };

  // 参数显示组件
  const renderParams = () => {
    if (!analyzedParams) return null;

    const params = [];

    if (analyzedParams.paper_size) {
      params.push(<Tag color="blue">纸张大小: {analyzedParams.paper_size}</Tag>);
    }
    if (analyzedParams.margin !== undefined) {
      params.push(<Tag color="green">边距: {analyzedParams.margin}mm</Tag>);
    }
    if (analyzedParams.auto_fit) {
      params.push(<Tag color="orange">自动适应</Tag>);
    }
    if (analyzedParams.center) {
      params.push(<Tag color="purple">居中</Tag>);
    }
    if (analyzedParams.grayscale) {
      params.push(<Tag color="gray">灰度</Tag>);
    }
    if (analyzedParams.monochrome) {
      params.push(<Tag color="black">黑白</Tag>);
    }
    if (analyzedParams.layers && analyzedParams.layers.length > 0) {
      params.push(<Tag color="cyan">图层: {analyzedParams.layers.join('、')}</Tag>);
    }

    return (
      <Card size="small" title={<><SettingOutlined /> 转换参数</>}>
        <Space wrap>
          {params.length > 0 ? params : <Text type="secondary">使用默认参数</Text>}
        </Space>
      </Card>
    );
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card title="DWG 转 PDF 智能转换器" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">

          {/* 第一步：上传文件 */}
          <Card size="small" title={<><CheckCircleOutlined /> 第一步：上传 DWG 文件</>}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload
                accept=".dwg"
                maxCount={1}
                onChange={handleFileChange}
                showUploadList={true}
                beforeUpload={() => false} // 阻止自动上传
              >
                <Button icon={<UploadOutlined />}>选择 DWG 文件</Button>
              </Upload>
              {dwgFile && (
                <Text type="success">
                  ✓ 已选择文件: {dwgFile.name}
                </Text>
              )}
            </Space>
          </Card>

          {/* 第二步：描述需求 */}
          <Card size="small" title={<><RobotOutlined /> 第二步：描述转换需求</>}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Paragraph>
                请用自然语言描述您的转换需求，留空则使用默认设置：
              </Paragraph>
              <ul>
                <li>我需要A3大小的PDF，黑白打印</li>
                <li>转换成灰度图，居中显示</li>
                <li>自动适应页面，留出10mm边距</li>
                <li>只导出"墙体"和"门窗"图层</li>
                <li>需要高清彩色PDF输出</li>
              </ul>

              <TextArea
                placeholder="请描述您的转换需求..."
                value={userRequest}
                onChange={(e) => setUserRequest(e.target.value)}
                rows={4}
                showCount
                maxLength={500}
              />

              <Button
                type="primary"
                icon={<RobotOutlined />}
                onClick={analyzeUserRequest}
                loading={isAnalyzing}
              >
                {isAnalyzing ? '分析中...' : (userRequest.trim() ? '分析需求' : '使用默认设置')}
              </Button>
            </Space>
          </Card>

          {/* 第三步：确认参数 */}
          {analyzedParams && (
            <Card size="small" title={<><CheckCircleOutlined /> 第三步：确认转换参数</>}>
              {renderParams()}
            </Card>
          )}

          {/* 第四步：开始转换 */}
          {analyzedParams && (
            <Card size="small" title={<><FilePdfOutlined /> 第四步：开始转换</>}>
              <Space direction="vertical" style={{ width: '100%' }}>
                {isConverting && (
                  <div style={{ textAlign: 'center' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>
                      <Progress percent={progress} />
                    </div>
                    <Text>正在转换中，请稍候...</Text>
                  </div>
                )}

                <Button
                  type="primary"
                  size="large"
                  onClick={startConversion}
                  disabled={!dwgFile || !analyzedParams || isConverting}
                  icon={<FilePdfOutlined />}
                >
                  {isConverting ? '转换中...' : '开始转换'}
                </Button>
              </Space>
            </Card>
          )}

        </Space>
      </Card>
    </div>
  );
};

export default DWGConverter;