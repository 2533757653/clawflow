import { Modal, Checkbox, Input, Space, message } from 'antd';
import { useState } from 'react';

interface SuggestionsModalProps {
  open: boolean;
  responsibilities: string[];
  onApply: (selected: string[]) => void;
  onCancel: () => void;
}

export default function SuggestionsModal({
  open,
  responsibilities,
  onApply,
  onCancel
}: SuggestionsModalProps) {
  const [selected, setSelected] = useState<string[]>(responsibilities);
  const [edited, setEdited] = useState<Record<number, string>>({});

  const handleOk = () => {
    const final = selected.map((s, i) => edited[i] !== undefined ? edited[i] : s).filter(s => s.trim());
    onApply(final);
    message.success('已应用建议');
  };

  const handleCancel = () => {
    setSelected([]);
    setEdited({});
    onCancel();
  };

  const toggleItem = (item: string) => {
    if (selected.includes(item)) {
      setSelected(selected.filter(s => s !== item));
    } else {
      setSelected([...selected, item]);
    }
  };

  const updateItem = (index: number, value: string) => {
    setEdited({ ...edited, [index]: value });
  };

  return (
    <Modal
      title="AI 职责建议"
      open={open}
      onOk={handleOk}
      onCancel={handleCancel}
      width={600}
    >
      <p style={{ marginBottom: 16, color: '#666' }}>
        以下是 AI 根据角色信息生成的职责建议，请勾选要应用的职责，您也可以编辑后再应用：
      </p>

      <div style={{ maxHeight: 400, overflow: 'auto', marginBottom: 16 }}>
        {responsibilities.map((item, index) => (
          <div key={index} style={{ marginBottom: 12, border: '1px solid #f0f0f0', padding: 12, borderRadius: 6 }}>
            <Space style={{ width: '100%' }} direction="vertical" size="small">
              <Checkbox
                checked={selected.includes(item)}
                onChange={() => toggleItem(item)}
              >
                {item}
              </Checkbox>
              {selected.includes(item) && (
                <Input
                  size="small"
                  value={edited[index] !== undefined ? edited[index] : item}
                  onChange={(e) => updateItem(index, e.target.value)}
                  placeholder="可编辑此职责"
                />
              )}
            </Space>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
        已选择 {selected.length} 项
      </div>
    </Modal>
  );
}