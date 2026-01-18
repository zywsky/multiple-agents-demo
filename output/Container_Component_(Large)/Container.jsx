// React Component Code
import React from 'react';
import { TextField } from '/Users/zyw/projects/ai-projects/multiple-agents/test_data/mui_library/packages/mui-material/src/TextField/TextField';
import { Checkbox } from '/Users/zyw/projects/ai-projects/multiple-agents/test_data/mui_library/packages/mui-material/src/Checkbox/Checkbox';

// 定义组件的props接口
interface ContainerProps {
  title: string;
  description: string;
  showActions: boolean;
  footerText: string;
}

const Container = ({ title, description, showActions, footerText }: ContainerProps) => {
  return (
    <div>
      <TextField label="Title" value={title} />
      <TextField label="Description" value={description} multiline />
      <Checkbox label="Show Actions" checked={showActions} />
      <TextField label="Footer Text" value={footerText} />
    </div>
  );
}

export default Container;