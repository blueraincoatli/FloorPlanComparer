import React, { useState } from 'react';
import { Upload, Button, message, Spin, Progress, Card, Typography, Space } from 'antd';
import { UploadOutlined, FilePdfOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;

interface EnhancedUploadFormProps {
  onJobCreated: (jobId: string) => void;
}

const EnhancedUploadForm: React.FC<EnhancedUploadFormProps> = ({ onJobCreated }) => {
  const [originFile, setOriginFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleOriginChange = (info: any) => {
    if (info.fileList.length > 0) {
      setOriginFile(info.fileList[0].originFileObj);
    } else {
      setOriginFile(null);
    }
  };

  const handleTargetChange = (info: any) => {
    if (info.fileList.length > 0) {
      setTargetFile(info.fileList[0].originFileObj);
    } else {
      setTargetFile(null);
    }
  };

  const handleSubmit = async () => {
    if (!originFile || !targetFile) {
      message.error('请上传两个DWG文件');
      return;
    }

    if (!originFile.name.toLowerCase().endsWith('.dwg') || 
        !targetFile.name.toLowerCase().endsWith('.dwg')) {
      message.error('请上传DWG文件');
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('origin_file', originFile);
      formData.append('target_file', targetFile);

      const response = await axios.post('/api/enhanced/process-dwg', formData, {
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
        message.success('文件上传成功，正在处理中...');
        onJobCreated(response.data.job_id);
      } else {
        message.error('处理失败');
      }
    } catch (error) {
      console.error('Upload error:', error);
      message.error('上传失败: ' + (error as any).message);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <Card title="增强版DWG文件比较" style={{ width: '100%' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Title level={4}>上传DWG文件</Title>
        
        <div>
          <Text strong>原始文件:</Text>
          <Upload 
            accept=".dwg" 
            maxCount={1}
            onChange={handleOriginChange}
            showUploadList={true}
          >
            <Button icon={<UploadOutlined />}>选择原始DWG文件</Button>
          </Upload>
        </div>

        <div>
          <Text strong>目标文件:</Text>
          <Upload 
            accept=".dwg" 
            maxCount={1}
            onChange={handleTargetChange}
            showUploadList={true}
          >
            <Button icon={<UploadOutlined />}>选择目标DWG文件</Button>
          </Upload>
        </div>

        {uploading && (
          <div style={{ textAlign: 'center' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Progress percent={progress} />
            </div>
            <Text>正在处理文件，请稍候...</Text>
          </div>
        )}

        <Button 
          type="primary" 
          onClick={handleSubmit} 
          disabled={!originFile || !targetFile || uploading}
          icon={<FilePdfOutlined />}
        >
          开始处理
        </Button>
      </Space>
    </Card>
  );
};

export default EnhancedUploadForm;