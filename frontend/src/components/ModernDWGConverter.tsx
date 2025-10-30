import React, { useState } from 'react';
import { Upload, Button, Card, Typography, Space, message, Alert } from 'antd';
import { UploadOutlined, FilePdfOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from "antd/es/upload/interface";
import axios from 'axios';

const { Title, Paragraph } = Typography;

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
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);

  // 处理文件上传
  const handleFileChange: UploadProps['onChange'] = ({ fileList: newFileList }) => {
    setFileList(newFileList);
  };

  // 开始转换
  const startConversion = async () => {
    if (fileList.length < 1) {
      message.error('请上传 DWG 文件');
      return;
    }

    const dwgFile = fileList[0].originFileObj;
    if (!dwgFile) {
      message.error('文件无效');
      return;
    }

    if (!dwgFile.name.toLowerCase().endsWith('.dwg')) {
      message.error('请上传 DWG 文件');
      return;
    }

    setIsConverting(true);
    setConversionError(null);

    try {
      // 使用默认参数
      const defaultParams: ConversionParams = {
        auto_fit: true,
        center: true,
        paper_size: null,
        margin: null,
        grayscale: false,
        monochrome: false,
        layers: null
      };

      const formData = new FormData();
      formData.append('dwg_file', dwgFile);
      formData.append('params', JSON.stringify(defaultParams));

      const response = await axios.post('/api/enhanced/convert-dwg', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.job_id) {
        message.success('转换任务已提交');
        onJobCreated(response.data.job_id);
      } else {
        message.error('转换失败');
      }
    } catch (error) {
      console.error('Conversion error:', error);
      const errorMessage = error instanceof Error ? error.message : '转换失败';
      setConversionError(errorMessage);
      message.error('转换失败: ' + errorMessage);
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '12px' }}>
        <Upload.Dragger
          multiple
          accept=".dwg"
          fileList={fileList}
          onChange={handleFileChange}
          beforeUpload={() => false}
          maxCount={1}
          showUploadList={{ showPreviewIcon: false, showRemoveIcon: true }}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">上传DWG图纸文件转换为PDF</p>
          <p className="ant-upload-hint">支持单个DWG文件</p>
        </Upload.Dragger>
      </div>
      
      <div style={{ marginTop: '16px', textAlign: 'center' }}>
        <Button 
          type="primary" 
          size="large"
          icon={<FilePdfOutlined />}
          onClick={startConversion}
          disabled={fileList.length < 1 || isConverting}
          loading={isConverting}
        >
          {isConverting ? '处理中...' : '开始转换'}
        </Button>
      </div>
      
      {conversionError && (
        <div style={{ marginTop: '12px' }}>
          <Alert message={conversionError} type="error" showIcon style={{ padding: '4px 12px' }} />
        </div>
      )}
    </div>
  );
};

export default ModernDWGConverter;