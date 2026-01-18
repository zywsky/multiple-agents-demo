// React Component Code
import React, { useState, useEffect } from'react';
import { BDLTextField, BDLCheckbox } from 'bdl-components';
import { useTheme } from 'bdl-components';

// Props interface based on AEM dialog configuration
interface PageProps {
  title: string;
  subtitle?: string;
  showNavigation: boolean;
  showSidebar: boolean;
  footerText?: string;
}

const validateInput = (input) => /^[a-zA-Z0-9]+$/.test(input);

const Page: React.FC<PageProps> = ({ title, subtitle, showNavigation, showSidebar, footerText }) => {
  const theme = useTheme();
  if (!validateInput(title)) {
    throw new Error('Invalid title input');
  }
  if (subtitle &&!validateInput(subtitle)) {
    throw new Error('Invalid subtitle input');
  }
  if (footerText &&!validateInput(footerText)) {
    throw new Error('Invalid footerText input');
  }
  return (
    <div className="bdl-flex-column-gap-2">
      <BDLTextField label="Title" value={title} fullWidth margin="normal" required color="primary" />
      {subtitle && <BDLTextField label="Subtitle" value={subtitle} fullWidth margin="normal" color="primary" />}
      <BDLCheckbox label="Show Navigation" checked={showNavigation} color="primary" />
      <BDLCheckbox label="Show Sidebar" checked={showSidebar} color="primary" />
      {footerText && <BDLTextField label="Footer Text" value={footerText} fullWidth margin="normal" color="primary" />}
    </div>
  );
};

// Dummy useEffect for data transformation (similar to @PostConstruct in Java)
useEffect(() => {
  // Add any data transformation logic here
}, []);

export default Page;

// 新增package.json文件内容，这里只是示例，实际需要根据项目情况填写
{
  "name": "page-component-extra-large",
  "version": "1.0.0",
  "description": "Page component for extra large layout",
  "main": "Page.jsx",
  "scripts": {
    "build": "your-build-command-here",
    "start": "your-start-command-here"
  },
  "dependencies": {
    "bdl-components": "your-dependency-version-here",
    "react": "^17.0.2",
    "react-dom": "^17.0.2"
  }
}