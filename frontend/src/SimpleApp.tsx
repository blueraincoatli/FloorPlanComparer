import { useState } from "react";
import { Upload, Table, Button, Spin, Alert, Segmented, Card } from "antd";
import { UploadOutlined, EyeOutlined, FilePdfOutlined, RobotOutlined } from "@ant-design/icons";
import type { UploadFile, UploadProps } from "antd/es/upload/interface";
import { useJobs } from "./hooks/useJobs";
import { DiffCanvas } from "./components/DiffCanvas";
import ModernDWGConverter from "./components/ModernDWGConverter";

export default function SimpleApp() {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [mode, setMode] = useState<'enhanced' | 'converter'>('enhanced');
  const {
    jobs,
    isLoadingJobs,
    jobsError,
    selectedJobId,
    diffPayload,
    isLoadingDiff,
    diffError,
    isUploading,
    uploadError,
    uploadSuccess,
    refreshJobs,
    selectJob,
    uploadFiles,
  } = useJobs();

  const handleUploadChange: UploadProps['onChange'] = ({ fileList: newFileList }) => {
    setFileList(newFileList);
  };

  const handleFileUpload = async () => {
    if (fileList.length < 2) {
      return;
    }

    const originalFile = fileList[0].originFileObj;
    const revisedFile = fileList[1].originFileObj;

    if (!originalFile || !revisedFile) {
      return;
    }

    // 调用useJobs中的uploadFiles方法
    await uploadFiles({ original: originalFile, revised: revisedFile });
    setFileList([]);  // 清空文件列表
  };

  const handleJobCreated = (jobId: string) => {
    // Refresh jobs to show the new job
    refreshJobs();
    // Select the new job
    selectJob(jobId);
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'jobId',
      key: 'jobId',
      width: 120,
      render: (text: string) => text.substring(0, 8) + '...',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 60,
      render: (status: string) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          queued: { text: "排队", color: "#1890ff" },
          processing: { text: "处理", color: "#faad14" },
          completed: { text: "完成", color: "#52c41a" },
          failed: { text: "失败", color: "#ff4d4f" },
        };
        const statusInfo = statusMap[status] || { text: status, color: "#000" };
        return <span style={{ color: statusInfo.color, fontSize: '12px' }}>{statusInfo.text}</span>;
      },
    },
    {
      title: '',
      key: 'action',
      width: 40,
      render: (_: any, record: any) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />} 
          onClick={() => selectJob(record.jobId)}
          size="small"
          style={{ padding: 0 }}
        />
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '24px', color: '#1890ff', fontSize: '24px' }}>图纸对比工具</h1>
      
      {/* 模式切换 */}
      <div style={{ marginBottom: '16px', textAlign: 'center' }}>
        <Segmented
          value={mode}
          onChange={setMode}
          options={[
            { 
              label: (
                <span>
                  <RobotOutlined /> 增强比对
                </span>
              ), 
              value: 'enhanced' 
            },
            { 
              label: (
                <span>
                  <FilePdfOutlined /> 图纸转PDF
                </span>
              ), 
              value: 'converter' 
            },
          ]}
        />
      </div>
      
      {/* 上方两栏：上传区域和任务列表 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        {/* 上传区域 */}
        <div>
          {mode === 'converter' ? (
            // 图纸转PDF模式
            <Card title="图纸转PDF" size="small">
              <ModernDWGConverter onJobCreated={handleJobCreated} />
            </Card>
          ) : (
            // 增强比对模式
            <Card title="上传图纸" size="small">
              <div style={{ marginBottom: '12px' }}>
                <Upload.Dragger
                  multiple
                  accept=".dwg"
                  fileList={fileList}
                  onChange={handleUploadChange}
                  beforeUpload={() => false}
                  maxCount={2}
                  showUploadList={{ showPreviewIcon: false, showRemoveIcon: true }}
                >
                  <p className="ant-upload-drag-icon">
                    <UploadOutlined />
                  </p>
                  <p className="ant-upload-text">上传原始图纸和施工图纸</p>
                  <p className="ant-upload-hint">支持同时上传两个DWG文件</p>
                </Upload.Dragger>
              </div>
              
              <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <Button 
                  type="primary" 
                  size="large"
                  onClick={handleFileUpload}
                  disabled={fileList.length < 2 || isUploading}
                  loading={isUploading}
                >
                  {isUploading ? '处理中...' : '开始增强比对'}
                </Button>
              </div>
              
              {(uploadError || uploadSuccess) && (
                <div style={{ marginTop: '12px' }}>
                  {uploadError && <Alert message={uploadError} type="error" showIcon style={{ padding: '4px 12px' }} />}
                  {uploadSuccess && <Alert message={uploadSuccess} type="success" showIcon style={{ padding: '4px 12px' }} />}
                </div>
              )}
            </Card>
          )}
        </div>
        
        {/* 任务列表 */}
        <div>
          <Card 
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>任务列表</span>
                <Button 
                  onClick={() => void refreshJobs()} 
                  loading={isLoadingJobs} 
                  size="small" 
                  type="text"
                  style={{ padding: '0 4px' }}
                >
                  刷新
                </Button>
              </div>
            } 
            size="small"
          >
            <div style={{ border: '1px solid #d9d9d9', borderRadius: '4px', overflow: 'hidden' }}>
              <Table 
                dataSource={jobs} 
                columns={columns} 
                pagination={false}
                loading={isLoadingJobs}
                rowKey="jobId"
                size="small"
                scroll={{ y: 200 }}
              />
            </div>
            
            {jobsError && <Alert message={jobsError} type="error" showIcon style={{ marginTop: '8px', padding: '4px 12px' }} />}
          </Card>
        </div>
      </div>
      
      {/* 下方整栏：差异结果 */}
      <div>
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{selectedJobId ? `差异结果 - ${selectedJobId.substring(0, 8)}...` : '差异结果'}</span>
            </div>
          } 
          size="small"
        >
          <div style={{ minHeight: '300px' }}>
            {isLoadingDiff ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <Spin tip="加载中..." />
              </div>
            ) : diffError ? (
              <Alert message={diffError} type="error" showIcon style={{ padding: '4px 12px' }} />
            ) : diffPayload ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '16px' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#52c41a' }}>{diffPayload.summary.added}</div>
                    <div style={{ fontSize: '12px', color: '#888' }}>新增</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff4d4f' }}>{diffPayload.summary.removed}</div>
                    <div style={{ fontSize: '12px', color: '#888' }}>删除</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#faad14' }}>{diffPayload.summary.modified}</div>
                    <div style={{ fontSize: '12px', color: '#888' }}>修改</div>
                  </div>
                </div>
                <DiffCanvas entities={diffPayload.entities} height={250} />
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#888', fontSize: '13px' }}>
                {selectedJobId ? '暂无差异数据' : '请选择任务查看结果'}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}