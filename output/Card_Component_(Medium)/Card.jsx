// React Component Code
import React, { useState, useEffect } from'react';
import { Card as BdlCard } from '/Users/zyw/projects/ai-projects/multiple-agents/test_data/mui_library/Card';
import { TextField as BdlTextField } from '/Users/zyw/projects/ai-projects/multiple-agents/test_data/mui_library/TextField';
import { Image as BdlImage } from '/Users/zyw/projects/ai-projects/multiple-agents/test_data/mui_library/Image';
import { Checkbox } from '/Users/zyw/projects/ai-projects/multiple-agents/test_data/mui_library/Checkbox';
import { styled } from '@mui/material/styles';

// Props interface based on the AEM dialog configuration
interface CardProps {
  title: string;
  description: string;
  imagePath: string;
  imageAlt: string;
  linkUrl: string;
  linkText: string;
  badge: string;
  cssClass: string;
  showFooter: boolean;
  openInNewTab: boolean;
  lazyLoad: boolean;
  tags: string[];
  buttonResource: string;
}

const StyledCard = styled(BdlCard)(({ theme }) => (
  {
    [theme.breakpoints.down('sm')]: {
      // 小屏幕样式
    }
  }
));

const Card: React.FC<CardProps> = ( {
  title,
  description,
  imagePath,
  imageAlt,
  linkUrl,
  linkText,
  badge,
  cssClass,
  showFooter,
  openInNewTab,
  lazyLoad,
  tags,
  buttonResource
} ) => {
  const [computedImageUrl, setComputedImageUrl] = useState('');
  const validateUrl = (url) => {
    const urlPattern = /^(https?:\/\/)?([\w-]+\.)+[\w-]+(\/[\w-./?%&=]*)*$/;
    return urlPattern.test(url);
  };
  const filteredLinkUrl = validateUrl(linkUrl)? linkUrl : '';
  const encodedLinkUrl = encodeURIComponent(filteredLinkUrl);

  useEffect(() => {
    // Here you can add any additional logic for computedImageUrl if needed
    setComputedImageUrl(imagePath);
  }, [imagePath]);

  const handleLinkClick = () => {
    // Add your link click logic here
    console.log('Link clicked');
  };

  return (
    <StyledCard className="card-container">
      <BdlTextField label="Title" value={title} />
      <BdlTextField label="Description" multiline value={description} />
      <BdlImage src={computedImageUrl} alt={imageAlt} lazyLoad={lazyLoad} />
      <BdlTextField label="Link URL" value={linkUrl} />
      <BdlTextField label="Link Text" value={linkText} />
      <BdlTextField label="Badge" value={badge} />
      <BdlTextField label="CSS Class" value={cssClass} />
      <Checkbox checked={showFooter} onChange={() => {}} />
      <Checkbox checked={openInNewTab} onChange={() => {}} />
      <BdlTextField label="Tags" multiline value={tags.join(', ')} />
      <BdlTextField label="Button Resource" value={buttonResource} />
      <a href={encodedLinkUrl} onClick={handleLinkClick} target={openInNewTab? '_blank' : '_self'}>{linkText}</a>
    </StyledCard>
  );
};

export default Card;